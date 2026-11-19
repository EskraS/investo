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
    fast: int = Field(ge=2, le=199)
    slow: int = Field(ge=3, le=200)
    commission_pct: float = Field(default=0.05, ge=0, le=1)
    position_pct: float = Field(default=5.0, ge=1, le=100)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/backtest")
def backtest(req: BacktestRequest):
    if req.ticker not in TICKERS:
        raise HTTPException(400, f"Unknown ticker. Allowed: {', '.join(TICKERS)}")
    if req.fast >= req.slow:
        raise HTTPException(400, "fast must be < slow")
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
