"""Performance metrics: pure functions over the equity curve.

The SAME functions run on strategy equity and on buy-and-hold equity.
They never read prices — the engine already built the curve.
"""

# CAGR and Sharpe both annualize with this. Define it once.
TRADING_DAYS = 252


def _points(equity):
    """Equity in bar order.

    A date-indexed Series looks up [0] and [-1] as labels. Callers pass
    either that Series or a plain list. Both become a list in bar order.
    """
    if hasattr(equity, "to_numpy"):
        return equity.to_numpy().tolist()
    return list(equity)


def total_return_pct(equity):
    """(final / initial - 1) * 100. `equity`: daily Series indexed by date."""
    points = _points(equity)
    if not points:
        return None
    initial = points[0]
    final = points[-1]
    return (final / initial - 1) * 100


def cagr_pct(equity):
    """((final / initial) ** (TRADING_DAYS / n_days) - 1) * 100.
    n_days = number of daily returns, not equity points."""
    points = _points(equity)
    if not points:
        return None
    n_days = len(points) - 1
    if n_days <= 0:
        return 0
    initial = points[0]
    final = points[-1]
    return ((final / initial) ** (TRADING_DAYS / n_days) - 1) * 100


def max_drawdown_pct(equity):
    """Worst peak-to-trough of the curve, * 100. Negative or zero.
    Running peak — one loop or cummax is the whole algorithm."""
    points = _points(equity)
    if not points:
        return None
    peak = points[0]
    worst = 0.0
    for value in points:
        if value > peak:
            peak = value
        if peak == 0:
            continue
        drawdown = value / peak - 1
        if drawdown < worst:
            worst = drawdown
    return worst * 100


def sharpe(equity):
    """mean(daily returns) / std(daily returns) * sqrt(TRADING_DAYS).
    Risk-free rate = 0. Population std (divide by n, not n-1), both curves.
    Zero volatility and a nonzero mean has no defined Sharpe: return None.
    A flat curve (mean 0 and std 0) returns 0."""
    points = _points(equity)
    if len(points) < 2:
        return None
    import math

    returns = [points[i] / points[i - 1] - 1 for i in range(1, len(points))]
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / n  # population
    if variance == 0:
        return 0 if mean == 0 else None
    return mean / math.sqrt(variance) * math.sqrt(TRADING_DAYS)


def win_rate_pct(trades):
    """Winning closed trades / all closed trades * 100. A win: return_pct > 0.

    Takes the TRADE LIST, not equity. Buy-and-hold never goes through here:
    its win_rate_pct is null and num_trades is 1 (see PLAN.md contract).
    No closed trades: return None — never raise, never report 0 wins."""
    if not trades:
        return None
    closed = [t for t in trades if "return_pct" in t]
    if not closed:
        return None
    wins = sum(1 for t in closed if t["return_pct"] > 0)
    return (wins / len(closed)) * 100
