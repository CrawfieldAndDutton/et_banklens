import { Check, Filter, Settings, Trash2, TrendingDown, TrendingUp, Share2, Phone } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { MonitoredCustomer, SignalItem } from '../api/types'

function iconFor(signalType: string, severity: string) {
  const t = signalType.toUpperCase()
  if (t.includes('SALARY') || severity === 'LOW')
    return { Icon: TrendingUp, className: 'bg-emerald-100 text-emerald-700' }
  if (t.includes('PAYMENT') || t.includes('BOUNCE') || severity === 'HIGH')
    return { Icon: TrendingDown, className: 'bg-red-100 text-red-700' }
  if (t.includes('DATA') || t.includes('CONSENT'))
    return { Icon: Share2, className: 'bg-sky-100 text-sky-700' }
  return { Icon: Phone, className: 'bg-violet-100 text-violet-700' }
}

export function NotificationsPage() {
  const [signals, setSignals] = useState<SignalItem[]>([])
  const [customers, setCustomers] = useState<MonitoredCustomer[]>([])
  const [readIds, setReadIds] = useState<Set<number>>(() => new Set())
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const [sigRes, custRes] = await Promise.all([
          api.fetchLatestSignals(1, 50),
          api.fetchMonitoredCustomers(1, 100),
        ])
        if (!cancelled) {
          setSignals(sigRes.items)
          setCustomers(custRes.items)
          const autoRead = new Set(
            sigRes.items.filter((s) => s.severity === 'LOW').map((s) => s.signal_id),
          )
          setReadIds(autoRead)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.detail : 'Failed to load')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const nameById = useMemo(() => {
    const m = new Map<number, string>()
    for (const c of customers) m.set(c.customer_id, c.display_name)
    return m
  }, [customers])

  const unreadCount = signals.filter((s) => !readIds.has(s.signal_id)).length

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-slate-900">Notifications</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setReadIds(new Set(signals.map((s) => s.signal_id)))}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
          >
            <Check className="size-4" />
            Mark All Read
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
          >
            <Settings className="size-4" />
            Settings
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2"
        >
          <Filter className="size-4" />
          Filter by: All Notifications
        </button>
        <span className="text-slate-400">{unreadCount} unread notifications</span>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <ul className="space-y-3">
        {signals.map((s) => {
          const unread = !readIds.has(s.signal_id)
          const { Icon, className } = iconFor(s.signal_type, s.severity)
          const cust = nameById.get(s.customer_id) ?? `Customer #${s.customer_id}`
          return (
            <li
              key={s.signal_id}
              className={`flex flex-wrap gap-4 rounded-xl border px-4 py-4 shadow-sm ${
                unread ? 'border-l-4 border-l-indigo-400 bg-indigo-50/40' : 'border-slate-200 bg-white'
              }`}
            >
              <div className={`flex size-10 shrink-0 items-center justify-center rounded-lg ${className}`}>
                <Icon className="size-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-slate-900">{s.signal_type.replaceAll('_', ' ')}</p>
                <p className="mt-0.5 text-sm text-slate-600">{s.narrative}</p>
                <p className="mt-2 text-xs text-slate-500">
                  Customer:{' '}
                  <Link to={`/customers/detail/${s.customer_id}`} className="font-medium text-indigo-600">
                    {cust}
                  </Link>
                </p>
              </div>
              <div className="flex flex-col items-end gap-2 text-xs text-slate-400">
                <span>{new Date(s.created_at).toLocaleString('en-IN')}</span>
                <div className="flex gap-1">
                  {unread && (
                    <button
                      type="button"
                      onClick={() =>
                        setReadIds((prev) => {
                          const n = new Set(prev)
                          n.add(s.signal_id)
                          return n
                        })
                      }
                      className="rounded p-1.5 hover:bg-slate-100"
                      aria-label="Mark read"
                    >
                      <Check className="size-4 text-slate-500" />
                    </button>
                  )}
                  <button type="button" className="rounded p-1.5 hover:bg-slate-100" aria-label="Dismiss">
                    <Trash2 className="size-4 text-slate-400" />
                  </button>
                </div>
              </div>
            </li>
          )
        })}
      </ul>
      {signals.length === 0 && !error && (
        <p className="text-center text-sm text-slate-500">No notifications.</p>
      )}

      <p className="text-xs text-slate-400">
        Feed is backed by compiled BSI signals (no separate notifications table in the API).
      </p>
    </div>
  )
}
