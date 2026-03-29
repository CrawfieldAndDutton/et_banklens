import { Filter, Plus, Search, Upload, Eye } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { CustomerDetail, MonitoredCustomer } from '../api/types'
import { bsiStatusBadge } from '../lib/customerUi'
import { formatInr } from '../lib/format'

type Segment = 'individual' | 'business'

export function CustomersPage() {
  const { pathname } = useLocation()
  const seg: Segment = pathname.includes('business') ? 'business' : 'individual'
  const [rows, setRows] = useState<MonitoredCustomer[]>([])
  const [details, setDetails] = useState<Record<number, CustomerDetail>>({})
  const [q, setQ] = useState('')
  const [error, setError] = useState<string | null>(null)

  const filteredType = seg === 'business' ? 'Business Loan' : null

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await api.fetchMonitoredCustomers(1, 100)
        let items = res.items
        if (filteredType) items = items.filter((c) => c.loan_type === filteredType)
        if (!cancelled) setRows(items)
        const detailEntries = await Promise.all(
          items.map(async (c) => {
            try {
              const d = await api.fetchCustomer(c.customer_id)
              return [c.customer_id, d] as const
            } catch {
              return [c.customer_id, null] as const
            }
          }),
        )
        if (!cancelled) {
          const map: Record<number, CustomerDetail> = {}
          for (const [id, d] of detailEntries) {
            if (d) map[id] = d
          }
          setDetails(map)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.detail : 'Failed to load customers')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [filteredType])

  const visible = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return rows
    return rows.filter(
      (r) =>
        r.display_name.toLowerCase().includes(needle) ||
        r.external_ref.toLowerCase().includes(needle),
    )
  }, [rows, q])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-slate-900">Customer Management</h1>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg border border-[#1a233a] bg-white px-4 py-2 text-sm font-medium text-[#1a233a]"
          >
            <Upload className="size-4" />
            Bulk Add Customer
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg bg-[#1a233a] px-4 py-2 text-sm font-medium text-white"
          >
            <Plus className="size-4" />
            Add Customer
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[240px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by name or customer ID"
            className="w-full rounded-lg border border-slate-200 py-2 pl-10 pr-3 text-sm outline-none ring-indigo-500/20 focus:border-indigo-300 focus:ring-2"
          />
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-lg border border-[#1a233a] bg-white px-4 py-2 text-sm font-medium text-[#1a233a]"
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
              <th className="px-5 py-3">Customer ID</th>
              <th className="px-5 py-3">Name</th>
              <th className="px-5 py-3">Contact</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Loan Amount</th>
              <th className="px-5 py-3">Type</th>
              <th className="px-5 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((c) => {
              const d = details[c.customer_id]
              const badge = bsiStatusBadge(c.last_bsi_status)
              const principal = d?.loan_snapshot?.principal_outstanding
              return (
                <tr key={c.customer_id} className="border-b border-slate-50 last:border-0">
                  <td className="px-5 py-3.5 font-mono text-xs text-slate-700">{c.external_ref}</td>
                  <td className="px-5 py-3.5 font-medium text-slate-900">{c.display_name}</td>
                  <td className="px-5 py-3.5 text-slate-600">
                    <div className="text-xs">{d?.email || '—'}</div>
                    <div className="text-xs text-slate-500">{c.phone_masked}</div>
                  </td>
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.className}`}>
                      {badge.label}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-slate-800">
                    {principal != null ? formatInr(principal) : '—'}
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">{c.loan_type}</td>
                  <td className="px-5 py-3.5 text-right">
                    <Link
                      to={`/customers/detail/${c.customer_id}`}
                      className="inline-flex rounded-lg p-2 text-indigo-600 hover:bg-indigo-50"
                      aria-label="View"
                    >
                      <Eye className="size-4" />
                    </Link>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {visible.length === 0 && !error && (
          <p className="p-8 text-center text-sm text-slate-500">No customers match this view.</p>
        )}
      </div>
    </div>
  )
}
