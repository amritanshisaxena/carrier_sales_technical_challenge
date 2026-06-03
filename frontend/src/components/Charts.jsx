import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, ArcElement, PointElement,
  Title, Tooltip, Legend,
} from 'chart.js'
import { Doughnut, Bar, Scatter } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, Title, Tooltip, Legend)
ChartJS.defaults.font.family = "'IBM Plex Sans', sans-serif"
ChartJS.defaults.color = '#56607a'

const palette = {
  booked: '#2563eb', no_agreement: '#f59e0b', declined: '#ef4444', not_eligible: '#8b5cf6',
  positive: '#10b981', neutral: '#6b7280', negative: '#ef4444', unknown: '#d1d5db',
}
const labelize = k => k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

function Panel({ title, subtitle, children }) {
  return (
    <div className="panel">
      <h3 className="text-[13px] font-semibold mb-1">{title}</h3>
      <div className="text-[11.5px] text-ink-soft mb-4">{subtitle}</div>
      <div className="relative h-[230px] min-h-[200px]">{children}</div>
    </div>
  )
}

function NoData() {
  return <div className="text-center text-ink-soft py-10 text-[13px]">No data yet</div>
}

const doughnutOpts = {
  cutout: '62%',
  maintainAspectRatio: false,
  responsive: true,
  plugins: { legend: { position: 'right', labels: { boxWidth: 12, padding: 14, font: { size: 12.5 } } } },
}

export default function Charts({ metrics, dashboardData, hrData }) {
  const outcomes = metrics.outcomes || {}
  const sentiment = metrics.sentiment || {}
  const oKeys = Object.keys(outcomes)
  const sKeys = Object.keys(sentiment)
  const runsData = hrData?.runs_per_day
  const statusCounts = hrData?.status_counts || {}
  const pickup = dashboardData.pickup_time_patterns
  const equipment = dashboardData.equipment_distribution
  const distance = dashboardData.distance_booking

  return (
    <>
      {/* Primary charts */}
      <div className="section-label">Breakdown</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-9">

        <Panel title="Call Outcomes" subtitle="Where each inbound call landed">
          {oKeys.length ? (
            <Doughnut
              data={{
                labels: oKeys.map(labelize),
                datasets: [{ data: oKeys.map(k => outcomes[k]), backgroundColor: oKeys.map(k => palette[k] || '#c9c2b4'), borderColor: '#fffdf8', borderWidth: 3 }],
              }}
              options={doughnutOpts}
            />
          ) : <NoData />}
        </Panel>

        <Panel title="Carrier Sentiment" subtitle="Tone of carriers across all calls">
          {sKeys.length ? (
            <Doughnut
              data={{
                labels: sKeys.map(labelize),
                datasets: [{ data: sKeys.map(k => sentiment[k]), backgroundColor: sKeys.map(k => palette[k] || '#c9c2b4'), borderColor: '#fffdf8', borderWidth: 3 }],
              }}
              options={doughnutOpts}
            />
          ) : <NoData />}
        </Panel>

        <Panel title="Runs Over Time" subtitle="Daily call volume — last 7 days (HappyRobot)">
          {runsData?.values?.some(v => v > 0) ? (
            <Bar
              data={{
                labels: runsData.labels,
                datasets: [{ label: 'Runs', data: runsData.values, backgroundColor: '#6366f1', borderRadius: 6, maxBarThickness: 40 }],
              }}
              options={{
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 } }, x: { grid: { display: false } } },
              }}
            />
          ) : <NoData />}
        </Panel>

        <Panel title="Completed vs Failed" subtitle="Agent reliability — HappyRobot run outcomes">
          {Object.keys(statusCounts).length ? (
            <Doughnut
              data={{
                labels: Object.keys(statusCounts).map(labelize),
                datasets: [{
                  data: Object.values(statusCounts),
                  backgroundColor: Object.keys(statusCounts).map(k =>
                    k === 'completed' ? '#10b981' : k === 'failed' ? '#ef4444' : '#9ca3af'
                  ),
                  borderColor: '#fffdf8',
                  borderWidth: 3,
                }],
              }}
              options={doughnutOpts}
            />
          ) : <NoData />}
        </Panel>
      </div>

      {/* Deep dive */}
      <div className="section-label">Deep Dive — Patterns at Scale</div>
      <div className="text-[12.5px] text-ink-soft mb-5">These charts become more insightful as call volume grows.</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-9">

        <Panel title="Pickup Time Patterns" subtitle="Booking outcome by time of day">
          {pickup?.booked?.some(v => v > 0) || pickup?.not_booked?.some(v => v > 0) ? (
            <Bar
              data={{
                labels: pickup.labels,
                datasets: [
                  { label: 'Booked', data: pickup.booked, backgroundColor: '#0ea5e9', borderRadius: 6, maxBarThickness: 60 },
                  { label: 'Not Booked', data: pickup.not_booked, backgroundColor: '#fbbf24', borderRadius: 6, maxBarThickness: 60 },
                ],
              }}
              options={{
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { boxWidth: 12, padding: 14 } } },
                scales: { y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 } }, x: { grid: { display: false } } },
              }}
            />
          ) : <NoData />}
        </Panel>

        <Panel title="Equipment Type Bookings" subtitle="Booking success by equipment type">
          {equipment?.labels?.length ? (
            <Bar
              data={{
                labels: equipment.labels,
                datasets: [
                  { label: 'Booked', data: equipment.booked, backgroundColor: '#14b8a6', borderRadius: 4 },
                  { label: 'Not Booked', data: equipment.not_booked, backgroundColor: '#a78bfa', borderRadius: 4 },
                ],
              }}
              options={{
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { boxWidth: 12, padding: 14 } } },
                scales: {
                  y: { beginAtZero: true, stacked: true, ticks: { stepSize: 1, precision: 0 } },
                  x: { stacked: true, grid: { display: false } },
                },
              }}
            />
          ) : <NoData />}
        </Panel>

        <Panel title="Distance vs Rate" subtitle="Does distance affect booking?">
          {distance?.booked?.length || distance?.not_booked?.length ? (
            <Scatter
              data={{
                datasets: [
                  { label: 'Booked', data: distance.booked, backgroundColor: '#2563eb', pointRadius: 7, pointHoverRadius: 10 },
                  { label: 'Not Booked', data: distance.not_booked, backgroundColor: '#f97316', pointRadius: 7, pointHoverRadius: 10, pointStyle: 'triangle' },
                ],
              }}
              options={{
                responsive: true, maintainAspectRatio: false,
                plugins: {
                  legend: { position: 'top', labels: { boxWidth: 12, padding: 14 } },
                  tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.x} mi, $${ctx.parsed.y}` } },
                },
                scales: {
                  x: { title: { display: true, text: 'Miles' }, beginAtZero: true },
                  y: { title: { display: true, text: 'Rate ($)' }, beginAtZero: true },
                },
              }}
            />
          ) : <NoData />}
        </Panel>
      </div>
    </>
  )
}
