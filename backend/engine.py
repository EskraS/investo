"""Backtest engine: SMA crossover, long-only, %-of-equity sizing.

Rules:
1. SMA on close. A signal on day t may use the close of day t;
   the fill is the OPEN of day t+1. No same-close fills.
2. Long only: one position at a time. No shorting.
3. On buy, deploy position_pct of current equity:
      notional = equity * (position_pct / 100)
      shares = notional / (fill_price * (1 + commission_rate))
   Idle cash stays. On sell, exit all shares. Default position_pct=5.
   position_pct=100 recovers classic all-in.
4. Commission on every buy and every sell. Unit: 0.05 = 0.05% -> x0.0005.
5. No trade before bar index `slow` — the slow SMA does not exist yet.
6. Still long on the last bar: sell at the last close, forced_close=True.
7. Buy-and-hold curve stays 100% invested from the first bar.

The loop is the product. Metrics and HTTP wait until the trades are right.
"""

INITIAL_CASH = 10_000.0


def run_backtest(df, fast: int, slow: int, commission_pct: float, position_pct: float = 5.0):
    """Run the simulation on `df` (output of data.get_ohlcv).

    Returns a dict with keys: equity_curve, trades, price, metrics.
    No ticker/params here — main.py wraps those around this dict.

    equity_curve: [{date, strategy, buyhold}] — both start at INITIAL_CASH.
    trades: [{entry_date, entry_price, exit_date, exit_price, return_pct,
             forced_close}] — fills are opens, except a forced exit (last close).
    price: [{date, open, close}] — one row per bar, ascending.
    metrics: placeholder until day 4 fills it via metrics.py.
    """
    rate = commission_pct / 100
    size = position_pct / 100

    df = df.reset_index(drop=True)
    dates = df["date"].dt.strftime("%Y-%m-%d").tolist()
    opens = df["open"].astype(float).tolist()
    closes = df["close"].astype(float).tolist()

    # NaN SMAs compare as False, so no signal can fire before both exist.
    above = (df["close"].rolling(fast).mean() > df["close"].rolling(slow).mean()).tolist()

    cash = INITIAL_CASH
    shares = 0.0
    entry = None
    pending = None
    trades = []
    strategy = []

    def close_position(i, price, forced):
        nonlocal cash, shares, entry
        cash += shares * price * (1 - rate)
        entry_i, entry_price = entry
        trades.append({
            "entry_date": dates[entry_i],
            "entry_price": entry_price,
            "exit_date": dates[i],
            "exit_price": price,
            "return_pct": (price * (1 - rate) / (entry_price * (1 + rate)) - 1) * 100,
            "forced_close": forced,
        })
        shares = 0.0
        entry = None

    for i in range(len(df)):
        # 1. Fill yesterday's signal at today's open.
        if pending == "buy":
            price = opens[i]
            notional = cash * size  # flat before a buy, so equity == cash
            shares = notional / (price * (1 + rate))
            cash -= shares * price * (1 + rate)
            entry = (i, price)
        elif pending == "sell":
            close_position(i, opens[i], forced=False)
        pending = None

        # 2. Read today's close for tomorrow's signal.
        was_above = above[i - 1] if i > 0 else False
        if shares == 0 and above[i] and not was_above:
            pending = "buy"
        elif shares > 0 and was_above and not above[i]:
            pending = "sell"

        strategy.append(cash + shares * closes[i])

    # A signal on the last bar has no t+1 open; exit any open position at the last close.
    if shares > 0:
        close_position(len(df) - 1, closes[-1], forced=True)
        strategy[-1] = cash

    first_close = closes[0]
    equity_curve = [
        {"date": d, "strategy": s, "buyhold": INITIAL_CASH * c / first_close}
        for d, s, c in zip(dates, strategy, closes)
    ]
    price = [{"date": d, "open": o, "close": c} for d, o, c in zip(dates, opens, closes)]

    return {
        "equity_curve": equity_curve,
        "trades": trades,
        "price": price,
        "metrics": {},
    }
