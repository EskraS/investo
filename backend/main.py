"""FastAPI app. Run from backend/:  uvicorn main:app --reload

Prove the process is up first: GET /api/health -> {"status": "ok"}.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data import TICKERS, get_ohlcv
from engine import run_backtest

app = FastAPI()

# Local dev only — this is the Vite port. Day 12: add the Vercel origin. Never "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BacktestRequest(BaseModel):
    ticker: str
    fast: int
    slow: int
    commission_pct: float = Field(default=0.05)
    position_pct: float = Field(default=5.0)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/backtest")
def backtest(req: BacktestRequest):
    if req.ticker not in TICKERS:
        raise HTTPException(400, f"Unknown ticker. Allowed: {', '.join(TICKERS)}")
    if req.fast < 2:
        raise HTTPException(400, "fast must be at least 2")
    if req.slow > 200:
        raise HTTPException(400, "slow must be at most 200")
    if req.fast >= req.slow:
        raise HTTPException(400, "fast must be < slow")
    if req.position_pct < 1 or req.position_pct > 100:
        raise HTTPException(400, "position_pct must be between 1 and 100")
    if req.commission_pct < 0 or req.commission_pct > 1:
        raise HTTPException(400, "commission_pct must be between 0 and 1")
    df = get_ohlcv(req.ticker)
    result = run_backtest(
        df, req.fast, req.slow, req.commission_pct, req.position_pct
    )
    # Wrap the engine dict so the body matches the contract in PLAN.md.
    return {
        "ticker": req.ticker,
        "params": {
            "fast": req.fast,
            "slow": req.slow,
            "commission_pct": req.commission_pct,
            "position_pct": req.position_pct,
        },
        **result,
    }
