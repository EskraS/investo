"""Day 1 spike: prove the math before Stooq, FastAPI, or React.

Three checks live here:
1. Hand-computed trades on ~20 fake OHLCV rows (cash, shares, equity per fill).
2. No lookahead: a signal on day t fills at the open of day t+1.
3. vectorbt cross-check on real aapl.us within 0.5% (local-only; NOT in
   requirements.txt).

The fake frame uses the same columns as data.get_ohlcv:
date, open, high, low, close, volume — ascending, no NaN rows.
"""

#delete everything above (for later)

import pandas as pd
import pytest
from engine import run_backtest


def make_ohlcv():
   return pd.DataFrame({
      "date": pd.date_range("2026-01-01", periods = 20, freq = "B"),
      "open": [5, 8, 9, 7, 12, 15, 20, 18, 14, 12, 16, 17, 18, 17, 20, 22, 25, 26, 25, 23],
      "high": [7.4, 9.5, 9.8, 10.6, 15.3, 20.8, 21.2, 18.6, 14.5, 16.4, 17.5, 18.4, 19.5, 19.8, 23.4, 27.6, 28.1, 26.8, 25.4, 25.7],
      "low": [4.6, 7.5, 5.7, 6.8, 11.4, 14.6, 18.3, 14.7, 12.2, 11.5, 15.6, 16.5, 17.4, 16.6, 19.5, 21.5, 24.2, 24.4, 22.6, 22.4],
      "close": [7, 9, 6, 10, 15, 20, 19, 15, 13, 16, 17, 18, 19, 19, 23, 27, 27, 25, 23, 25],
      "volume": [1000] * 20,
   })

def test_ohlcv_fixture_shape():
   df = make_ohlcv()
   assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
   assert len(df) == 20
   assert not df.isna().any().any()

def test_first_buy_hand_computed():
   df = make_ohlcv()
   df["fast"] = df["close"].rolling(2).mean()
   df["slow"] = df["close"].rolling(3).mean()

   i = 2 #first index where both SMAs exist

   assert df["fast"].iloc[i] > df["slow"].iloc[i]
   fill_price = df["open"].iloc[i + 1]
   assert fill_price == 7

   equity = 10_000.0
   position_pct = 5.0
   rate = 0.05 * 0.01
   notional = equity * (position_pct / 100)
   shares = notional / (fill_price * (1 + rate))
   cash = equity - shares * fill_price * (1 + rate)

   assert notional == 500
   assert abs(shares - 71.39287499107589) < 1e-9
   assert abs(cash - 9500) < 1e-9


def test_first_sell_hand_computed():
   df = make_ohlcv()
   df["fast"] = df["close"].rolling(2).mean()
   df["slow"] = df["close"].rolling(3).mean()

   shares = 71.39287499107589
   cash = 9500.0
   rate = 0.0005

   i = 3
   assert df["fast"].iloc[i] < df["slow"].iloc[i]
   assert df["fast"].iloc[i-1] > df["slow"].iloc[i-1]

   sell_price = df["open"].iloc[i+1]
   assert sell_price == 12
   
   proceeds = shares * sell_price * (1 - rate)
   new_balance = cash + proceeds
   assert abs(proceeds - 856.2861426429643) < 1e-9
   assert abs(new_balance - 10356.286142642964) < 1e-9

def test_second_buy_hand_computed():
   df = make_ohlcv()
   df["fast"] = df["close"].rolling(2).mean()
   df["slow"] = df["close"].rolling(3).mean()

   i = 4

   assert df["fast"].iloc[i] > df["slow"].iloc[i]
   fill_price = df["open"].iloc[i+1]
   assert fill_price == 15

   equity = 10356.286142642964
   position_pct = 5.0
   rate = 0.05 * 0.01
   notional = equity * (position_pct / 100)
   shares = 34.50370195783097
   cash = equity - shares * fill_price * (1 + rate)

   assert abs(notional - 517.8143071321482) < 1e-9
   assert abs(cash - 9838.471835510816) < 1e-9

def test_second_sell_hand_computed():
   df =make_ohlcv()
   df["fast"] = df["close"].rolling(2).mean()
   df["slow"] = df["close"].rolling(3).mean()

   i = 7
   assert df["fast"].iloc[i] < df["slow"].iloc[i]

   equity = 9838.471835510816
   shares = 34.50370195783097
   rate = 0.0005

   sell_price = df["open"].iloc[i+1]
   assert sell_price == 14

   proceeds = shares * sell_price * (1 - rate)
   assert abs(proceeds - 482.8103014959288) < 1e-9
   cash = equity + proceeds

   assert abs(cash - 10321.282137006745) < 1e-9

def test_third_buy_hand_computed():
   df = make_ohlcv()
   df["fast"] = df["close"].rolling(2).mean()
   df["slow"] = df["close"].rolling(3).mean()

   i = 10
   assert df["fast"].iloc[i] > df["slow"].iloc[i]
   assert df["fast"].iloc[i-1] < df["slow"].iloc[i-1]

   fill_price = df["open"].iloc[i+1]
   assert fill_price == 17

   equity = 10321.282137006745
   position_pct = 5.0
   rate = 0.0005
   notional = equity * (position_pct / 100)
   shares = notional / (fill_price * (1 + rate))
   cash = equity - shares * fill_price * (1 + rate)

   assert abs(notional - 516.0641068503372) < 1e-9
   assert abs(shares - 30.341541396968417) < 1e-9
   assert abs(cash - 9805.218030156408) < 1e-9

def test_third_sell_hand_computed():
   df = make_ohlcv()
   df["fast"] = df["close"].rolling(2).mean()
   df["slow"] = df["close"].rolling(3).mean()

   i = 17
   assert df["fast"].iloc[i] < df["slow"].iloc[i]
   assert df["fast"].iloc[i-1] > df["slow"].iloc[i-1]

   sell_price = df["open"].iloc[i+1]
   assert sell_price == 25

   cash = 9805.218030156408
   shares = 30.341541396968417
   rate = 0.0005
   proceeds = shares * sell_price * (1 - rate)

   assert abs(proceeds - 758.1592656567484) < 1e-9
   assert abs(cash + proceeds - 10563.377295813156) < 1e-9


# --- Day 3: the real engine must reproduce the hand-computed trades ---

def test_engine_matches_hand_computed_trades():
   result = run_backtest(make_ohlcv(), fast=2, slow=3, commission_pct=0.05, position_pct=5)
   trades = result["trades"]

   assert [(t["entry_price"], t["exit_price"]) for t in trades] == [(7, 12), (15, 14), (17, 25)]
   assert not any(t["forced_close"] for t in trades)
   assert trades[1]["return_pct"] < 0 < trades[0]["return_pct"]
   assert abs(result["equity_curve"][-1]["strategy"] - 10563.377295813156) < 1e-9

def test_engine_no_lookahead():
   df = make_ohlcv()
   result = run_backtest(df, fast=2, slow=3, commission_pct=0.05, position_pct=5)
   dates = df["date"].dt.strftime("%Y-%m-%d").tolist()

   # Signals on bars 2, 4, 10 (buy) and 3, 7, 17 (sell) fill on the next bar's open.
   assert [t["entry_date"] for t in result["trades"]] == [dates[3], dates[5], dates[11]]
   assert [t["exit_date"] for t in result["trades"]] == [dates[4], dates[8], dates[18]]

def test_engine_marks_to_market_between_fills():
   result = run_backtest(make_ohlcv(), fast=2, slow=3, commission_pct=0.05, position_pct=5)
   curve = result["equity_curve"]

   # Bar 3: bought 71.39... shares at the open of 7, cash 9500, close 10.
   assert abs(curve[3]["strategy"] - (9500 + 71.39287499107589 * 10)) < 1e-6
   assert curve[0]["strategy"] == curve[0]["buyhold"] == 10_000.0
   assert abs(curve[-1]["buyhold"] - 10_000.0 * 25 / 7) < 1e-9

def test_engine_forced_close_at_last_close():
   closes = list(range(10, 30))
   df = pd.DataFrame({
      "date": pd.date_range("2026-01-01", periods=20, freq="B"),
      "open": [c - 0.5 for c in closes],
      "high": [c + 1 for c in closes],
      "low": [c - 1 for c in closes],
      "close": closes,
      "volume": [1000] * 20,
   })
   result = run_backtest(df, fast=2, slow=3, commission_pct=0, position_pct=100)
   (trade,) = result["trades"]

   assert trade["forced_close"] is True
   assert trade["entry_price"] == 12.5  # signal bar 2, fill open of bar 3
   assert trade["exit_price"] == 29     # last close
   assert abs(result["equity_curve"][-1]["strategy"] - 10_000 * 29 / 12.5) < 1e-9


# --- Day 1 cross-check: same strategy in vectorbt on real data ---

def test_vectorbt_cross_check_aapl():
   vbt = pytest.importorskip("vectorbt")
   from data import get_ohlcv

   try:
      df = get_ohlcv("aapl.us")
   except Exception as exc:
      pytest.skip(f"no market data available: {exc}")

   fast, slow, commission_pct, position_pct = 20, 50, 0.05, 5
   result = run_backtest(df, fast, slow, commission_pct, position_pct)

   above = df["close"].rolling(fast).mean() > df["close"].rolling(slow).mean()
   was_above = above.shift(1, fill_value=False)
   entries = (above & ~was_above).shift(1, fill_value=False)
   exits = (~above & was_above).shift(1, fill_value=False)

   pf = vbt.Portfolio.from_signals(
      close=df["close"], entries=entries, exits=exits, price=df["open"],
      size=position_pct / 100, size_type="percent", fees=commission_pct / 100,
      init_cash=10_000.0, freq="1D",
   )

   ours = result["equity_curve"][-1]["strategy"]
   theirs = float(pf.final_value())
   assert len(result["trades"]) == int(pf.trades.count())
   assert abs(ours / theirs - 1) < 0.005

