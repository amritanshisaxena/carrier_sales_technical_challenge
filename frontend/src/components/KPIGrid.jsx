export default function KPIGrid({ metrics, hrData }) {
  const totalRuns = hrData?.total_runs ?? metrics.total_calls
  const completed = hrData?.status_counts?.completed ?? 0
  const reliability = totalRuns > 0 ? ((completed / totalRuns) * 100).toFixed(1) : null

  const kpis = [
    { title: 'Total Calls', value: totalRuns, sub: 'from HappyRobot' },
    { title: 'Booking Rate', value: `${(metrics.booking_rate * 100).toFixed(1)}%`, sub: 'calls to booked loads' },
    { title: 'Avg Margin Delta', value: metrics.avg_margin_delta != null ? `$${Math.round(metrics.avg_margin_delta)}` : '—', sub: 'agreed vs loadboard' },
    { title: 'Avg Agreed Rate', value: metrics.avg_agreed_rate != null ? `$${Math.round(metrics.avg_agreed_rate)}` : '—', sub: 'on booked loads' },
    { title: 'Avg Rounds', value: metrics.avg_negotiation_rounds ?? '—', sub: 'to reach a decision' },
    { title: 'FMCSA Rejected', value: metrics.not_eligible_count, sub: 'ineligible carriers' },
  ]

  if (hrData?.avg_duration_display) {
    kpis.push({ title: 'Avg Call Duration', value: hrData.avg_duration_display, sub: 'from HappyRobot' })
  }

  if (reliability != null) {
    kpis.push({ title: 'Agent Reliability', value: `${reliability}%`, sub: 'completed runs' })
  }

  return (
    <>
      <div className="section-label">Operations Snapshot</div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3.5 mb-9">
        {kpis.map((k, i) => (
          <div
            key={i}
            className="kpi panel relative overflow-hidden"
            style={{ animationDelay: `${0.04 + i * 0.06}s` }}
          >
            <div className="absolute top-0 left-0 w-full h-[3px] bg-accent" />
            <div className="text-[11.5px] text-ink-soft font-semibold uppercase tracking-wide mb-2.5">
              {k.title}
            </div>
            <div className="font-mono text-2xl sm:text-3xl font-semibold tracking-tight leading-none">
              {k.value}
            </div>
            <div className="text-[11.5px] text-ink-soft mt-2 font-mono">{k.sub}</div>
          </div>
        ))}
      </div>
    </>
  )
}
