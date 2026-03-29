import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { SignalItem } from '../api/types'
import { severityUi } from '../lib/customerUi'

export function MonitoringPage() {
  const [items, setItems] = useState<SignalItem[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await api.fetchLatestSignals(1, 100)
        if (!cancelled) setItems(res.items)
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.detail : 'Failed to load signals')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-900">Monitoring</h1>
      <p className="text-sm text-slate-500">
        Latest compiled signals from <code className="rounded bg-slate-100 px-1">/api/v1/signals/latest</code>.
      </p>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <th className="px-5 py-3">Signal</th>
              <th className="px-5 py-3">Customer</th>
              <th className="px-5 py-3">Severity</th>
              <th className="px-5 py-3">When</th>
              <th className="px-5 py-3 text-right">Open</th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => {
              const sev = severityUi(s.severity)
              return (
                <tr key={s.signal_id} className="border-b border-slate-50 last:border-0">
                  <td className="px-5 py-3.5">
                    <p className="font-medium text-slate-900">{s.signal_type.replaceAll('_', ' ')}</p>
                    <p className="text-xs text-slate-500">{s.narrative}</p>
                  </td>
                  <td className="px-5 py-3.5 text-slate-700">#{s.customer_id}</td>
                  <td className="px-5 py-3.5">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${sev.className}`}>
                      {sev.label}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-xs text-slate-500">
                    {new Date(s.created_at).toLocaleString('en-IN')}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <Link
                      to={`/customers/detail/${s.customer_id}`}
                      className="text-xs font-medium text-indigo-600 hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {items.length === 0 && !error && (
          <p className="p-8 text-center text-sm text-slate-500">No signals yet.</p>
        )}
      </div>
    </div>
  )
}
