import { useState } from 'react'
import BacktestForm from './components/BacktestForm'
import EquityChart from './components/EquityChart'
import PriceChart from './components/PriceChart'
import MetricsPanel from './components/MetricsPanel'
import { runBacktest } from './api'

export default function App() {
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleRun(params) {
    setLoading(true)
    setError(null)
    try {
      setResult(await runBacktest(params))
    } catch (e) {
      setError(e.message)
      setResult(null) // a failed run must not leave yesterday's chart on screen
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <h1>SMA Backtester</h1>
      <BacktestForm onRun={handleRun} loading={loading} />
      {error && <p role="alert">{error}</p>}
      {result && (
        <>
          <EquityChart data={result.equity_curve} />
          <PriceChart price={result.price} trades={result.trades} />
          <MetricsPanel metrics={result.metrics} />
        </>
      )}
    </main>
  )
}
