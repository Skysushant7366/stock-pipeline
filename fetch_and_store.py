"""
fetch_and_store.py
==================
Fetches stock data from Yahoo Finance → writes to PostgreSQL.
Sends a summary email after every run.

Run manually:        python fetch_and_store.py
Task Scheduler runs: C:\\path\\to\\python.exe  C:\\path\\to\\fetch_and_store.py

Requirements (install once):
    pip install yfinance pandas psycopg2-binary sqlalchemy python-dotenv
"""

import logging
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import yfinance as yf

# ── Load config ───────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from config import DB_CONFIG, TICKERS, LOOKBACK_DAYS, LOG_FILE, EMAIL_FROM, EMAIL_TO, EMAIL_APP_PWD

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_conn():
    """Return a fresh psycopg2 connection."""
    return psycopg2.connect(**DB_CONFIG)


def ensure_schema(conn):
    """Create tables/views if not present (idempotent)."""
    schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
    if schema_path.exists():
        sql = schema_path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            statements = [s.strip() for s in sql.split(";") if s.strip()
                          and not s.strip().upper().startswith("-- ")]
            for stmt in statements:
                try:
                    cur.execute(stmt)
                except Exception:
                    conn.rollback()
        conn.commit()
        log.info("Schema verified.")


# ── Fetch from Yahoo Finance ──────────────────────────────────────────────────

def fetch_prices(tickers, lookback_days):
    end   = datetime.today()
    start = end - timedelta(days=lookback_days)
    log.info("Fetching %d tickers  %s -> %s ...", len(tickers), start.date(), end.date())

    try:
        raw = yf.download(
            tickers,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception as e:
        log.error("yfinance download failed: %s", e)
        return pd.DataFrame()

    frames = []
    for ticker in tickers:
        try:
            df = raw.copy() if len(tickers) == 1 else raw[ticker].copy()
            df = df.dropna(subset=["Close"])
            if df.empty:
                log.warning("No data for %s", ticker)
                continue
            df = df.reset_index().rename(columns={
                "Date":      "date",
                "Open":      "open",
                "High":      "high",
                "Low":       "low",
                "Close":     "close",
                "Adj Close": "adj_close",
                "Volume":    "volume",
            })
            df["ticker"] = ticker
            df["date"]   = pd.to_datetime(df["date"]).dt.date
            frames.append(df[["ticker","date","open","high","low","close","adj_close","volume"]])
        except Exception as exc:
            log.warning("Parse error for %s: %s", ticker, exc)

    if not frames:
        log.error("No data returned from yfinance.")
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    log.info("Fetched %d rows total.", len(out))
    return out


# ── Technical indicators ──────────────────────────────────────────────────────

def _rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def compute_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    results = []
    for ticker, g in prices.groupby("ticker"):
        g = g.sort_values("date").copy()
        g["daily_return"]   = g["close"].pct_change()
        g["volatility_7d"]  = g["daily_return"].rolling(7).std()
        g["volatility_30d"] = g["daily_return"].rolling(30).std()
        g["sma_10"]         = g["close"].rolling(10).mean()
        g["sma_50"]         = g["close"].rolling(50).mean()
        g["sma_200"]        = g["close"].rolling(200).mean()
        g["rsi_14"]         = _rsi(g["close"])
        g["volume_avg_10"]  = g["volume"].rolling(10).mean()
        results.append(g[["ticker","date","daily_return","volatility_7d",
                           "volatility_30d","sma_10","sma_50","sma_200",
                           "rsi_14","volume_avg_10"]])
    return pd.concat(results, ignore_index=True)


# ── Upsert to PostgreSQL ──────────────────────────────────────────────────────

def _safe(v):
    try:
        if pd.isna(v): return None
    except Exception: pass
    return float(v) if v is not None else None


def upsert_prices(conn, prices: pd.DataFrame) -> int:
    rows = [
        (r.ticker, r.date,
         _safe(r.open), _safe(r.high), _safe(r.low),
         _safe(r.close), _safe(r.adj_close), int(r.volume or 0))
        for _, r in prices.iterrows()
    ]
    sql = """
        INSERT INTO stock_prices (ticker, date, open, high, low, close, adj_close, volume)
        VALUES %s
        ON CONFLICT (ticker, date) DO UPDATE SET
            open      = EXCLUDED.open,
            high      = EXCLUDED.high,
            low       = EXCLUDED.low,
            close     = EXCLUDED.close,
            adj_close = EXCLUDED.adj_close,
            volume    = EXCLUDED.volume,
            fetched_at= NOW()
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    log.info("Upserted %d price rows.", len(rows))
    return len(rows)


def upsert_metrics(conn, metrics: pd.DataFrame):
    rows = [
        (r.ticker, r.date,
         _safe(r.daily_return), _safe(r.volatility_7d), _safe(r.volatility_30d),
         _safe(r.sma_10), _safe(r.sma_50), _safe(r.sma_200),
         _safe(r.rsi_14), _safe(r.volume_avg_10))
        for _, r in metrics.iterrows()
    ]
    sql = """
        INSERT INTO stock_metrics
            (ticker, date, daily_return, volatility_7d, volatility_30d,
             sma_10, sma_50, sma_200, rsi_14, volume_avg_10)
        VALUES %s
        ON CONFLICT (ticker, date) DO UPDATE SET
            daily_return   = EXCLUDED.daily_return,
            volatility_7d  = EXCLUDED.volatility_7d,
            volatility_30d = EXCLUDED.volatility_30d,
            sma_10         = EXCLUDED.sma_10,
            sma_50         = EXCLUDED.sma_50,
            sma_200        = EXCLUDED.sma_200,
            rsi_14         = EXCLUDED.rsi_14,
            volume_avg_10  = EXCLUDED.volume_avg_10,
            computed_at    = NOW()
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    log.info("Upserted %d metric rows.", len(rows))


def log_run(conn, tickers, fetched, inserted, status, error=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO pipeline_runs (tickers, rows_fetched, rows_inserted, status, error_msg)
            VALUES (%s, %s, %s, %s, %s)
        """, (",".join(tickers), fetched, inserted, status, error))
    conn.commit()


# ── Email Summary ─────────────────────────────────────────────────────────────

def send_summary_email(status, rows_inserted, error=None):
    body = f"""
Stock Pipeline Run Summary
──────────────────────────
Date    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status  : {status}
Tickers : {', '.join(TICKERS)}
Rows    : {rows_inserted}
Error   : {error or 'None'}

──────────────────────────
Sent automatically by your Stock Pipeline
    """
    msg = MIMEText(body)
    msg['Subject'] = f"[Stock Pipeline] {status} — {datetime.today().date()}"
    msg['From']    = EMAIL_FROM
    msg['To']      = EMAIL_TO

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(EMAIL_FROM, EMAIL_APP_PWD)
            s.send_message(msg)
        log.info("Summary email sent to %s", EMAIL_TO)
    except Exception as e:
        log.warning("Email failed (pipeline still ran fine): %s", e)


# ── Main ─────────────────────────────────────────────────────────────────────

def run():
    log.info("=" * 60)
    log.info("Stock fetch started  --  %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("Tickers: %s", ", ".join(TICKERS))

    conn = None
    rows_fetched = rows_inserted = 0
    status = "FAILED"
    error  = None

    try:
        conn = get_conn()
        ensure_schema(conn)

        prices  = fetch_prices(TICKERS, LOOKBACK_DAYS)
        if prices.empty:
            raise RuntimeError("No price data fetched.")

        metrics = compute_metrics(prices)
        rows_fetched  = len(prices)
        rows_inserted = upsert_prices(conn, prices)
        upsert_metrics(conn, metrics)
        status = "SUCCESS"

    except Exception as exc:
        error = str(exc)
        log.exception("Pipeline error: %s", exc)
    finally:
        if conn:
            try:
                log_run(conn, TICKERS, rows_fetched, rows_inserted, status, error)
            except Exception:
                pass
            send_summary_email(status, rows_inserted, error)  # ← sends email every run
            conn.close()

    log.info("Done. Status=%s  Rows=%d", status, rows_inserted)
    print(f"\n{ '[OK]' if status=='SUCCESS' else '[FAIL]'}  {status}  |  "
          f"Fetched={rows_fetched}  Inserted={rows_inserted}")


if __name__ == "__main__":
    run()
