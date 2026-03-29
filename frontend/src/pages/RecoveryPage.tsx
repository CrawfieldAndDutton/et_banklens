import { Filter, Phone, Search, Sparkles, History, ChevronDown } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { CustomerDetail, MonitoredCustomer } from '../api/types'
import { formatInr } from '../lib/format'

type Row = {
  customer: MonitoredCustomer
  detail: CustomerDetail | null
}

function priorityFromDpd(dpd: number): { label: string; className: string } {
  if (dpd >= 30) return { label: 'High', className: 'bg-red-100 text-red-800' }
  if (dpd >= 10) return { label: 'Medium', className: 'bg-sky-100 text-sky-800' }
  return { label: 'Low', className: 'bg-slate-100 text-slate-700' }
}

export function RecoveryPage() {
  const [rows, setRows] = useState<Row[]>([])
  const [tab, setTab] = useState<'tocall' | 'history'>('tocall')
  const [q, setQ] = useState('')
  const [openMenu, setOpenMenu] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await api.fetchMonitoredCustomers(1, 100)
        const enriched = await Promise.all(
          res.items.map(async (c) => {
            try {
              const d = await api.fetchCustomer(c.customer_id)
              return { customer: c, detail: d }
            } catch {
              return { customer: c, detail: null }
            }
          }),
        )
        if (!cancelled) setRows(enriched)
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.detail : 'Failed to load recovery queue')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const toCall = useMemo(() => {
    return rows.filter((r) => (r.detail?.loan_snapshot?.dpd_days ?? 0) > 0)
  }, [rows])

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase()
    const base = tab === 'tocall' ? toCall : rows
    if (!needle) return base
    return base.filter(
      (r) =>
        r.customer.display_name.toLowerCase().includes(needle) ||
        r.customer.external_ref.toLowerCase().includes(needle),
    )
  }, [rows, toCall, tab, q])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-slate-900">Recovery Calling Agent</h1>
        <div className="flex flex-wrap items-center gap-2">
          <select className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
            <option>English</option>
          </select>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg bg-[#1a233a] px-4 py-2 text-sm font-medium text-white"
          >
            <Phone className="size-4" />
            Start New Call
          </button>
        </div>
      </div>

      <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-1">
        <button
          type="button"
          onClick={() => setTab('tocall')}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            tab === 'tocall' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
          }`}
        >
          To Call
        </button>
        <button
          type="button"
          onClick={() => setTab('history')}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            tab === 'history' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
          }`}
        >
          Call History
        </button>
      </div>

      {tab === 'tocall' && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative min-w-[220px] flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search by name or ID"
                className="w-full rounded-lg border border-slate-200 py-2 pl-10 pr-3 text-sm outline-none focus:border-indigo-300 focus:ring-2 focus:ring-indigo-100"
              />
            </div>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm"
            >
              <Filter className="size-4" />
              Filter
            </button>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-3">Customer</th>
                  <th className="px-5 py-3">Contact</th>
                  <th className="px-5 py-3">Amount Due</th>
                  <th className="px-5 py-3">Days Overdue</th>
                  <th className="px-5 py-3">Priority</th>
                  <th className="px-5 py-3">Last Contact</th>
                  <th className="px-5 py-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => {
                  const loan = r.detail?.loan_snapshot
                  const dpd = loan?.dpd_days ?? 0
                  const pri = priorityFromDpd(dpd)
                  const due = loan?.principal_outstanding
                  return (
                    <tr key={r.customer.customer_id} className="border-b border-slate-50 last:border-0">
                      <td className="px-5 py-3.5">
                        <p className="font-semibold text-slate-900">{r.customer.display_name}</p>
                        <p className="text-xs text-slate-500">{r.customer.external_ref}</p>
                      </td>
                      <td className="px-5 py-3.5 text-slate-600">{r.customer.phone_masked}</td>
                      <td className="px-5 py-3.5">{due != null ? formatInr(due) : '—'}</td>
                      <td className="px-5 py-3.5">{dpd > 0 ? `${dpd} days` : '—'}</td>
                      <td className="px-5 py-3.5">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${pri.className}`}>
                          {pri.label}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-500">—</td>
                      <td className="px-5 py-3.5">
                        <div className="relative inline-block text-left">
                          <button
                            type="button"
                            onClick={() =>
                              setOpenMenu((id) => (id === r.customer.customer_id ? null : r.customer.customer_id))
                            }
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2 py-1 text-xs"
                          >
                            Actions
                            <ChevronDown className="size-3" />
                          </button>
                          {openMenu === r.customer.customer_id && (
                            <div className="absolute right-0 z-20 mt-1 w-56 rounded-lg border border-slate-200 bg-white py-2 shadow-xl">
                              {(
                                [
                                  ['WhatsApp', 'text-emerald-600'],
                                  ['SMS', 'text-sky-600'],
                                  ['Call', 'text-violet-600'],
                                  ['Email', 'text-orange-600'],
                                ] as const
                              ).map(([ch, color]) => (
                                <div key={ch} className="px-3 py-1">
                                  <p className={`text-[10px] font-bold uppercase ${color}`}>{ch}</p>
                                  <button
                                    type="button"
                                    className="flex w-full items-center gap-2 py-1 text-left text-xs text-slate-700 hover:bg-slate-50"
                                  >
                                    <Sparkles className="size-3.5 text-amber-500" />
                                    Trigger AI Conversation
                                  </button>
                                  <Link
                                    to={`/customers/detail/${r.customer.customer_id}`}
                                    className="flex items-center gap-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
                                    onClick={() => setOpenMenu(null)}
                                  >
                                    <History className="size-3.5" />
                                    View History
                                  </Link>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {filtered.length === 0 && !error && (
              <p className="p-8 text-center text-sm text-slate-500">
                No customers with overdue days in loan snapshot.
              </p>
            )}
          </div>
        </>
      )}

      {tab === 'history' && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-sm text-slate-500 shadow-sm">
          Call transcripts are not stored by this API. Use{' '}
          <Link className="text-indigo-600" to="/customers/individual">
            customer detail → Calls
          </Link>{' '}
          for outbound message previews.
        </div>
      )}
    </div>
  )
}
