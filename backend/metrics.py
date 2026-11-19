"""Performance metrics: pure functions over the equity curve.

The SAME functions run on strategy equity and on buy-and-hold equity.
They never read prices — the engine already built the curve.
"""

# CAGR and Sharpe both annualize with this. Define it once.
TRADING_DAYS = 252


def total_return_pct(equity):
    """(final / initial - 1) * 100. `equity`: daily Series indexed by date."""
    ...


def cagr_pct(equity):
    """((final / initial) ** (TRADING_DAYS / n_days) - 1) * 100.
    n_days = number of daily returns, not equity points."""
    ...


def max_drawdown_pct(equity):
    """Worst peak-to-trough of the curve, * 100. Negative or zero.
    Running peak — one loop or cummax is the whole algorithm."""
    ...


def sharpe(equity):
    """mean(daily returns) / std(daily returns) * sqrt(TRADING_DAYS).
    Risk-free rate = 0. Pick sample vs population std; use it for BOTH curves."""
    ...


def win_rate_pct(trades):
    """Winning closed trades / all closed trades * 100. A win: return_pct > 0.

    Takes the TRADE LIST, not equity. Buy-and-hold never goes through here:
    its win_rate_pct is null and num_trades is 1 (see PLAN.md contract).
    No closed trades: return None — never raise, never report 0 wins."""
    ...
