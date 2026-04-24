-- ============================================================
-- STOCK DATA PIPELINE — Database Schema
-- ============================================================

-- Core price history (OHLCV)
CREATE TABLE IF NOT EXISTS stock_prices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker        TEXT    NOT NULL,
    date          DATE    NOT NULL,
    open          REAL,
    high          REAL,
    low           REAL,
    close         REAL,
    adj_close     REAL,
    volume        INTEGER,
    fetched_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

-- Daily summary metrics (computed by the Python processor)
CREATE TABLE IF NOT EXISTS stock_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT    NOT NULL,
    date            DATE    NOT NULL,
    daily_return    REAL,          -- (close - prev_close) / prev_close
    volatility_7d   REAL,          -- 7-day rolling std of returns
    volatility_30d  REAL,          -- 30-day rolling std of returns
    sma_10          REAL,          -- 10-day simple moving average
    sma_50          REAL,          -- 50-day simple moving average
    sma_200         REAL,          -- 200-day simple moving average
    rsi_14          REAL,          -- 14-day RSI
    volume_avg_10   REAL,          -- 10-day average volume
    computed_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

-- Pipeline run audit log
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    tickers       TEXT,            -- comma-separated list
    rows_fetched  INTEGER,
    rows_inserted INTEGER,
    status        TEXT,            -- SUCCESS | PARTIAL | FAILED
    error_msg     TEXT
);

-- ============================================================
-- Useful query views
-- ============================================================

CREATE VIEW IF NOT EXISTS latest_prices AS
SELECT  sp.*
FROM    stock_prices sp
JOIN    (
    SELECT ticker, MAX(date) AS max_date
    FROM   stock_prices
    GROUP  BY ticker
) mx ON sp.ticker = mx.ticker AND sp.date = mx.max_date;

CREATE VIEW IF NOT EXISTS price_with_metrics AS
SELECT
    sp.ticker,
    sp.date,
    sp.open, sp.high, sp.low, sp.close, sp.volume,
    sm.daily_return,
    sm.sma_10, sm.sma_50, sm.sma_200,
    sm.volatility_7d, sm.volatility_30d,
    sm.rsi_14
FROM stock_prices sp
LEFT JOIN stock_metrics sm USING (ticker, date)
ORDER BY sp.ticker, sp.date;
