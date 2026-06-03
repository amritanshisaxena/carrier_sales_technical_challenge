import { useState, useEffect } from 'react'
import KPIGrid from './components/KPIGrid'
import Charts from './components/Charts'
import CallsTable from './components/CallsTable'

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/dashboard')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-ink-soft text-sm font-mono animate-pulse">Loading dashboard…</div>
    </div>
  )

  if (error) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="panel text-center p-8">
        <div className="text-bad font-semibold mb-2">Failed to load dashboard</div>
        <div className="text-ink-soft text-sm">{error}</div>
      </div>
    </div>
  )

  const { metrics, calls, dashboard_data, hr_data } = data

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6">
      <header className="border-b-2 border-ink mb-8 pt-7 pb-4">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end gap-3">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 border-2 border-ink rounded-lg grid place-items-center font-bold text-lg bg-ink text-paper shrink-0">A</div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold tracking-tight">Acme Logistics · Inbound Carrier Desk</h1>
              <div className="text-xs text-ink-soft font-medium uppercase tracking-widest">AI Carrier Sales — Live Operations</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://platform.happyrobot.ai/fdeamritanshisaxena/workflows/io14uwgjyb6n/editor/6r2dr6pzc0p4"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-semibold text-accent hover:underline inline-flex items-center gap-1"
            >
              View in HappyRobot
              <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
            <div className="flex items-center gap-2 text-xs font-semibold text-ink-soft font-mono">
              <span className="w-2.5 h-2.5 rounded-full bg-good shadow-[0_0_0_4px_rgba(47,125,82,.15)]" /> LIVE
            </div>
          </div>
        </div>
      </header>

      <KPIGrid metrics={metrics} hrData={hr_data} />
      <Charts metrics={metrics} dashboardData={dashboard_data} hrData={hr_data} />
      <CallsTable calls={calls} />
    </div>
  )
}
