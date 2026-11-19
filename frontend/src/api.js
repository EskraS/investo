// Single API client. The base URL is baked in at build time:
// import.meta.env.VITE_API_URL is replaced when Vite builds.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function runBacktest({ ticker, fast, slow, commission_pct, position_pct }) {
  const res = await fetch(`${API_URL}/api/backtest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker, fast, slow, commission_pct, position_pct }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Request failed: ${res.status}`)
  }
  return res.json()
}
