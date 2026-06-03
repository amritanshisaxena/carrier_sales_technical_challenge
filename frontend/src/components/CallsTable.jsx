import { useState } from 'react'
import DetailModal from './DetailModal'

const pillClass = {
  booked: 'bg-blue-50 text-blue-700',
  no_agreement: 'bg-amber-50 text-amber-700',
  declined: 'bg-red-50 text-red-600',
  not_eligible: 'bg-purple-50 text-purple-700',
}
const sentimentClass = {
  positive: 'text-emerald-600',
  neutral: 'text-gray-500',
  negative: 'text-red-500',
}

const headers = ['Time', 'MC #', 'Carrier', 'Load', 'Outcome', 'Agreed', 'Rounds', 'Sentiment', 'Duration', 'Status', 'Details']

export default function CallsTable({ calls }) {
  const [selected, setSelected] = useState(null)

  return (
    <>
      <div className="section-label">Recent Calls</div>
      <div className="panel mb-9">
        {calls.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-[13px] border-collapse">
              <thead>
                <tr>
                  {headers.map(h => (
                    <th key={h} className="text-[11px] uppercase tracking-wide text-ink-soft font-semibold px-3 pb-2.5 border-b border-line text-left whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {calls.map((c, i) => (
                  <tr key={i} className="hover:bg-paper/50 transition-colors">
                    <td className="px-3 py-2.5 border-b border-line font-mono text-[12.5px] whitespace-nowrap">{c.created_at}</td>
                    <td className="px-3 py-2.5 border-b border-line font-mono text-[12.5px] whitespace-nowrap">{c.mc_number || '—'}</td>
                    <td className="px-3 py-2.5 border-b border-line text-[12.5px] whitespace-nowrap">{c.carrier_name || '—'}</td>
                    <td className="px-3 py-2.5 border-b border-line font-mono text-[12.5px] whitespace-nowrap">{c.load_id || '—'}</td>
                    <td className="px-3 py-2.5 border-b border-line whitespace-nowrap">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold ${pillClass[c.outcome] || 'bg-gray-100 text-gray-600'}`}>
                        {(c.outcome || '—').replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 border-b border-line font-mono text-[12.5px] whitespace-nowrap">
                      {c.agreed_rate ? `$${Math.round(c.agreed_rate)}` : '—'}
                    </td>
                    <td className="px-3 py-2.5 border-b border-line font-mono text-[12.5px] whitespace-nowrap">
                      {c.negotiation_rounds ?? '—'}
                    </td>
                    <td className="px-3 py-2.5 border-b border-line whitespace-nowrap">
                      <span className={`text-[12.5px] font-semibold ${sentimentClass[c.sentiment] || 'text-gray-400'}`}>
                        {c.sentiment || '—'}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 border-b border-line font-mono text-[12.5px] whitespace-nowrap">{c.duration || '—'}</td>
                    <td className="px-3 py-2.5 border-b border-line font-mono text-[12.5px] whitespace-nowrap">{c.run_status || '—'}</td>
                    <td className="px-3 py-2.5 border-b border-line text-[12.5px] whitespace-nowrap">
                      <button
                        onClick={() => setSelected(c)}
                        className="text-accent font-semibold hover:underline cursor-pointer bg-transparent border-0 p-0 text-[12.5px] inline-flex items-center gap-1"
                      >
                        View
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6v6H9z"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center text-ink-soft py-10 text-[13px]">
            No calls captured yet. Place a test web call and they'll appear here automatically.
          </div>
        )}
      </div>

      {selected && <DetailModal call={selected} onClose={() => setSelected(null)} />}
    </>
  )
}
