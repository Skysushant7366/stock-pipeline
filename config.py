# ============================================================
#  config.py  —  Passwords are now stored in .env file
#                Never hardcode passwords here!
# ============================================================

from dotenv import load_dotenv
import os

load_dotenv()  # reads from .env file automatically

# ── PostgreSQL connection ─────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "stockdb",
    "user":     "postgres",
    "password": os.getenv("DB_PASSWORD"),   # ← reads from .env
}

# ── Tickers to track ─────────────────────────────────────────
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "TSLA", "META",  "JPM",   "V",   "RELIANCE.NS",
]

# ── How many days of history to fetch each run ───────────────
LOOKBACK_DAYS = 90

# ── Email settings ───────────────────────────────────────────
EMAIL_FROM    = os.getenv("EMAIL_FROM")
EMAIL_TO      = os.getenv("EMAIL_TO")
EMAIL_APP_PWD = os.getenv("EMAIL_APP_PWD")

# ── Log file location ────────────────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(__file__), "fetch.log")
