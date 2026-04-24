# Stock Market Data Pipeline 📈

> An end-to-end automated stock data pipeline that fetches, stores, analyses and alerts — daily, without manual intervention.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?style=flat&logo=postgresql)
![Automation](https://img.shields.io/badge/Automation-Windows%20Task%20Scheduler-green?style=flat)
![Status](https://img.shields.io/badge/Pipeline-Active-brightgreen?style=flat)

---

## What This Project Does

Every day at 6 PM this pipeline automatically:

1. **Fetches** latest OHLCV data for 10 stocks from Yahoo Finance
2. **Computes** 8 technical indicators per stock (RSI, SMA, volatility etc.)
3. **Stores** everything in a structured PostgreSQL database
4. **Logs** every run with status, rows fetched and any errors
5. **Emails** a summary report — no manual action needed

---

## Stocks Tracked

| US Tech | US Finance | India |
|---|---|---|
| AAPL, MSFT, GOOGL | JPM, V | RELIANCE.NS |
| AMZN, NVDA | | |
| TSLA, META | | |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data Source | Yahoo Finance (yfinance) |
| Language | Python 3.10+ |
| Database | PostgreSQL 15 |
| DB Driver | psycopg2, SQLAlchemy |
| Indicators | pandas (custom RSI, SMA) |
| Alerts | SMTP via Gmail |
| Scheduling | Windows Task Scheduler |
| Security | python-dotenv (.env) |
| Visualisation | Jupyter Notebook, matplotlib, mplfinance |

---

## Architecture

```
Yahoo Finance API
      │
      ▼
fetch_and_store.py
      │
      ├──► stock_prices table    (OHLCV data)
      │
      ├──► stock_metrics table   (RSI, SMA, volatility)
      │
      ├──► pipeline_runs table   (audit log)
      │
      └──► Email Summary         (Gmail alert)

Windows Task Scheduler → runs daily at 18:00 IST automatically
```

---

## Technical Indicators Computed

| Indicator | Description |
|---|---|
| `daily_return` | Day-over-day % price change |
| `volatility_7d` | 7-day rolling standard deviation |
| `volatility_30d` | 30-day rolling standard deviation |
| `sma_10` | 10-day Simple Moving Average |
| `sma_50` | 50-day Simple Moving Average |
| `sma_200` | 200-day Simple Moving Average |
| `rsi_14` | 14-period Relative Strength Index |
| `volume_avg_10` | 10-day average trading volume |

---

## Database Schema

```sql
stock_prices     — OHLCV + fetched_at timestamp
stock_metrics    — All 8 indicators per ticker per date
pipeline_runs    — Every run logged with status + error
```

Full schema: [`schema.sql`](schema.sql)

---

## Visualisations (Jupyter Notebook)

The notebook `stock_visuals_upgrade.ipynb` generates:

- **Return Correlation Matrix** — heatmap showing how stocks move together
- **Period Summary** — annualised returns ranked best to worst
- **Candlestick Charts** — 60-day OHLC with volume
- **Buy/Sell Signals** — SMA-10 × SMA-50 crossover strategy
- **Volume Spike Detection** — flags days with 2x average volume
- **Daily Gainers vs Losers** — latest day performance bar chart
- **Pipeline Audit Log** — recent run history with status

---

## Email Alert Sample

```
Stock Pipeline Run Summary
──────────────────────────
Date    : 2026-04-24 18:00:05
Status  : SUCCESS
Tickers : AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, JPM, V, RELIANCE.NS
Rows    : 616
Error   : None
```

---

## Project Structure

```
stock_pipeline/
├── fetch_and_store.py       # Main pipeline script
├── config.py                # Settings (reads from .env)
├── schema.sql               # PostgreSQL table definitions
├── setup_task_scheduler.bat # One-time Windows automation setup
├── stock_visuals_upgrade.ipynb  # Analysis & visualisation notebook
├── .env                     # Secrets (not uploaded to GitHub)
└── .gitignore               # Blocks .env from version control
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Skysushant7366/stock-pipeline.git
cd stock-pipeline
```

### 2. Install dependencies
```bash
pip install yfinance pandas psycopg2-binary sqlalchemy python-dotenv
```

### 3. Create PostgreSQL database
```bash
psql -U postgres -c "CREATE DATABASE stockdb;"
psql -U postgres -d stockdb -f schema.sql
```

### 4. Create `.env` file
```
DB_PASSWORD=your_postgres_password
EMAIL_FROM=your@gmail.com
EMAIL_TO=your@gmail.com
EMAIL_APP_PWD=your_gmail_app_password
```

### 5. Run manually
```bash
python fetch_and_store.py
```

### 6. Schedule automation (Windows)
```
Right click setup_task_scheduler.bat → Run as Administrator
```

---

## Pipeline Audit Log (Sample)

| run_at | status | rows_fetched | rows_inserted | error_msg |
|---|---|---|---|---|
| 2026-04-24 18:00:05 | SUCCESS | 616 | 616 | None |
| 2026-04-24 17:00:04 | SUCCESS | 616 | 616 | None |
| 2026-04-23 18:00:03 | FAILED | 615 | 615 | object of type 'int' has no len() |

---

## Key Findings (April 2026 Analysis)

- **Best performer:** NVDA +34.75% annualised return
- **Worst performer:** TSLA -55.33% annualised return
- **Highest correlation:** AMZN ↔ GOOGL (0.65) — move almost in sync
- **Best diversifier:** RELIANCE.NS — correlation below 0.10 with most US stocks
- **AAPL signal:** SMA-10 crossed above SMA-50 in mid-April — active BUY signal

---

## Security

- All credentials stored in `.env` file
- `.env` is blocked from GitHub via `.gitignore`
- Gmail App Password used (not real Gmail password)
- No hardcoded secrets anywhere in codebase

---

## Author

**Sushant Kumar Yadav**  
Data Analyst | Business Analyst | Financial Analyst

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat&logo=linkedin)](https://linkedin.com/in/sushantkumaryadav310899)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?style=flat&logo=github)](https://github.com/Skysushant7366)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-orange?style=flat)](https://skysushant7366.github.io/Sushant-portfolio/)

---

*Pipeline runs automatically every day at 18:00 IST via Windows Task Scheduler*
