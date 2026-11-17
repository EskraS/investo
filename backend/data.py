"""Data loading and caching.

One job: ticker in, clean daily bars out.
get_ohlcv checks SQLite first: if the ticker's table exists and its newest
row is less than 7 days old, read it and return. Otherwise download from
Yahoo Finance, write the table, and return. The 7-day rule is the whole
freshness policy. If the download fails but a stale table exists, the stale
table is returned, so a second call works offline. The engine never talks
to the network.

Stooq's CSV endpoint now serves a JavaScript bot check to scripts, so the
download goes through yfinance. Tickers keep the Stooq-style ".us" suffix.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

DB_PATH = Path(__file__).parent / "data" / "cache.db"  # gitignored; mkdir if missing
HISTORY = "10y"
MAX_AGE = timedelta(days=7)
COLUMNS = ["date", "open", "high", "low", "close", "volume"]

TICKERS = [  # whitelist: ten hardcoded symbols — anything else is an error
    "aapl.us", "msft.us", "googl.us", "amzn.us", "nvda.us",
    "spy.us", "qqq.us", "meta.us", "tsla.us", "jpm.us",
]


def get_ohlcv(ticker: str):
    """Return daily bars for `ticker` as a DataFrame.

    Columns: date (datetime64), open, high, low, close, volume (floats).
    Sorted ascending, no NaN rows. main.py already checked the ticker
    against TICKERS. An empty frame is a bug, not a successful download.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    table = ticker.replace(".", "_")

    with sqlite3.connect(DB_PATH) as conn:
        cached = _read_cache(conn, table)
        if cached is not None and datetime.now() - cached["date"].iloc[-1] < MAX_AGE:
            return cached

        try:
            df = _download(ticker)
        except Exception:
            if cached is not None:
                return cached
            raise

        df.to_sql(table, conn, if_exists="replace", index=False)
        return df


def _read_cache(conn, table):
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if not exists:
        return None
    df = pd.read_sql(f'SELECT * FROM "{table}" ORDER BY date', conn, parse_dates=["date"])
    return df if not df.empty else None


def _download(ticker: str):
    symbol = ticker.split(".")[0].upper()
    raw = yf.download(symbol, period=HISTORY, interval="1d", auto_adjust=True, progress=False)
    if raw is None or raw.empty:
        raise ValueError(f"No data returned for {ticker}")

    # yfinance returns (field, symbol) MultiIndex columns even for one symbol.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw.reset_index().rename(columns=str.lower)[COLUMNS]
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df[COLUMNS[1:]] = df[COLUMNS[1:]].astype(float)
    df = df.dropna().sort_values("date").drop_duplicates("date").reset_index(drop=True)
    if df.empty:
        raise ValueError(f"No clean rows for {ticker}")
    return df
