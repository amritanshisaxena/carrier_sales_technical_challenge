import { useEffect, Fragment } from 'react'

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

export default function DetailModal({ call, onClose }) {
  useEffect(() => {
    const handler = e => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handler)
      document.body.style.overflow = ''
    }
  }, [onClose])

  const val = v => (v != null && v !== '') ? v : '—'

  const rows = [
    ['Run ID', <span className="font-mono text-[11.5px]">{val(call.run_id)}</span>],
    ['Time', <span className="font-mono">{val(call.created_at)}</span>],
    ['MC Number', <span className="font-mono">{val(call.mc_number)}</span>],
    ['Carrier', val(call.carrier_name)],
    ['Load ID', <span className="font-mono">{val(call.load_id)}</span>],
    ['Outcome', (
      <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold ${pillClass[call.outcome] || 'bg-gray-100 text-gray-600'}`}>
        {(call.outcome || '—').replace(/_/g, ' ')}
      </span>
    )],
    ['Agreed Rate', val(call.agreed_rate != null ? `$${Math.round(call.agreed_rate)}` : null)],
    ['Loadboard Rate', val(call.loadboard_rate != null ? `$${Math.round(call.loadboard_rate)}` : null)],
    ['Negotiation Rounds', val(call.negotiation_rounds)],
    ['Sentiment', (
      <span className={`font-semibold ${sentimentClass[call.sentiment] || 'text-gray-400'}`}>
        {val(call.sentiment)}
      </span>
    )],
    ['Duration', val(call.duration)],
    ['Status', val(call.run_status)],
  ]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(20,33,61,.45)', backdropFilter: 'blur(4px)' }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-card border border-line rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto animate-[rise_0.25s_ease]">
        <div className="flex items-center justify-between px-6 pt-5 pb-3 border-b border-line">
          <h3 className="text-[15px] font-bold">Call Details</h3>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-gray-100 grid place-items-center text-ink-soft text-lg bg-transparent border-0 cursor-pointer"
          >
            &times;
          </button>
        </div>
        <div className="px-6 py-4 space-y-3 text-[13px]">
          <div className="grid grid-cols-2 gap-x-6 gap-y-2.5">
            {rows.map(([label, value], i) => (
              <Fragment key={i}>
                <div className="text-ink-soft font-semibold text-[11.5px] uppercase tracking-wide">{label}</div>
                <div>{value}</div>
              </Fragment>
            ))}
          </div>
          {call.transcript && (
            <div className="mt-4 pt-4 border-t border-line">
              <div className="text-ink-soft font-semibold text-[11.5px] uppercase tracking-wide mb-2">Transcript</div>
              <div className="bg-paper rounded-lg p-3 text-[12.5px] leading-relaxed max-h-48 overflow-y-auto font-mono whitespace-pre-wrap">
                {call.transcript}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
