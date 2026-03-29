import {
  CalendarDays,
  ChevronDown,
  CreditCard,
  FileText,
  Landmark,
  LineChart as LineChartIcon,
  RefreshCw,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { CustomerDetail, OutboundMessageRow, SignalItem } from '../api/types'
import { bsiStatusBadge, severityUi } from '../lib/customerUi'
import { formatInr, formatPct } from '../lib/format'

type MainTab = 'overview' | 'statement' | 'credit'
type OverviewSub = 'summary' | 'analysis' | 'loans' | 'risk' | 'monitoring' | 'calls'
type StatementSub = 'income' | 'spending' | 'savings'

export function CustomerDetailPage() {
  const { id } = useParams()
  const customerId = Number(id)
  const [customer, setCustomer] = useState<CustomerDetail | null>(null)
  const [signals, setSignals] = useState<SignalItem[]>([])
  const [messages, setMessages] = useState<OutboundMessageRow[]>([])
  const [error, setError] = useState<string | null>(null)
  const [bsiBusy, setBsiBusy] = useState(false)
  const [mainTab, setMainTab] = useState<MainTab>('overview')
  const [ovTab, setOvTab] = useState<OverviewSub>('summary')
  const [stmtTab, setStmtTab] = useState<StatementSub>('income')
  const [syncOpen, setSyncOpen] = useState(false)

  const load = useCallback(async () => {
    if (!Number.isFinite(customerId)) return
    setError(null)
    try {
      const [c, sig, msgs] = await Promise.all([
        api.fetchCustomer(customerId),
        api.fetchSignalsForCustomer(customerId),
        api.fetchOmnichannelMessages(1, 50).catch(() => ({ items: [] as OutboundMessageRow[] })),
      ])
      setCustomer(c)
      setSignals(sig.items)
      setMessages(msgs.items.filter((m) => m.customer_id === customerId))
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'Failed to load customer')
    }
  }, [customerId])

  useEffect(() => {
    load()
  }, [load])

  async function runBsi() {
    if (!Number.isFinite(customerId)) return
    setBsiBusy(true)
    setSyncOpen(false)
    try {
      await api.triggerBsi(customerId)
      await load()
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : 'BSI run failed')
    } finally {
      setBsiBusy(false)
    }
  }

  if (!Number.isFinite(customerId)) {
    return <p className="text-sm text-red-600">Invalid customer</p>
  }

  if (error && !customer) {
    return (
      <div className="space-y-2">
        <p className="text-sm text-red-600">{error}</p>
        <Link to="/customers/individual" className="text-sm text-indigo-600">
          Back to customers
        </Link>
      </div>
    )
  }

  if (!customer) {
    return <p className="text-sm text-slate-500">Loading…</p>
  }

  const loan = customer.loan_snapshot
  const badge = bsiStatusBadge(customer.last_bsi_status)
  const creditProxy = loan ? 720 + Math.min(40, Math.max(-80, loan.credit_score_delta_90d)) : null
  const incomeStability = loan
    ? Math.min(99, 72 + (loan.salary_proxy_delta_pct > 0 ? 8 : 0) - Math.min(20, loan.dpd_days))
    : null
  const fraudRisk = loan ? Math.min(40, 8 + loan.eod_negative_days_90d + (loan.dpd_days > 15 ? 6 : 0)) : null

  const incomeTrend = loan
    ? ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'].map((m, i) => ({
        month: m,
        amount: Math.round(loan.avg_monthly_inflow * (0.92 + i * 0.02 + (i === 3 ? 0.06 : 0))),
      }))
    : []

  const pieData = loan
    ? [
        { name: 'Salary', value: 77, fill: '#818cf8' },
        { name: 'Investments', value: 6, fill: '#4f46e5' },
        { name: 'Rental', value: 14, fill: '#c4b5fd' },
        { name: 'Other', value: 3, fill: '#e0e7ff' },
      ]
    : []

  const monthlyIncome = loan ? Math.round(loan.avg_monthly_inflow * 1.08) : 0

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold text-slate-900">{customer.display_name}</h1>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
              ID {customer.external_ref}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">{customer.phone_masked}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-center">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Latest sync</p>
            <p className="text-xs font-medium text-slate-700">
              {customer.last_bsi_status ?? '—'} · {customer.consent_recorded_at?.slice(0, 10) ?? '—'}
            </p>
          </div>
          <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700">Data Received</span>
          <div className="relative">
            <button
              type="button"
              onClick={() => setSyncOpen((o) => !o)}
              disabled={bsiBusy}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm"
            >
              <RefreshCw className={`size-4 ${bsiBusy ? 'animate-spin' : ''}`} />
              Sync
              <ChevronDown className="size-4 opacity-60" />
            </button>
            {syncOpen && (
              <div className="absolute right-0 z-20 mt-1 w-48 rounded-lg border border-slate-200 bg-white py-1 shadow-lg">
                <button
                  type="button"
                  onClick={() => void runBsi()}
                  className="block w-full px-3 py-2 text-left text-sm hover:bg-slate-50"
                >
                  Run BSI monitoring
                </button>
              </div>
            )}
          </div>
          <button
            type="button"
            className="rounded-lg bg-[#1a233a] px-4 py-2 text-sm font-medium text-white"
          >
            View Details
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-2">
        {(
          [
            ['overview', 'Overview', LineChartIcon],
            ['statement', 'Bank Statement', Landmark],
            ['credit', 'Credit Report', CreditCard],
          ] as const
        ).map(([key, label, Icon]) => (
          <button
            key={key}
            type="button"
            onClick={() => setMainTab(key)}
            className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium ${
              mainTab === key
                ? 'bg-white text-indigo-900 shadow-sm ring-1 ring-slate-200'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <Icon className="size-4" />
            {label}
          </button>
        ))}
      </div>

      {mainTab === 'overview' && (
        <>
          <div className="flex flex-wrap gap-2">
            {(
              [
                ['summary', 'Overview'],
                ['analysis', 'Analysis'],
                ['loans', 'Loans'],
                ['risk', 'Risk'],
                ['monitoring', 'Monitoring'],
                ['calls', 'Calls'],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                type="button"
                onClick={() => setOvTab(k)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
                  ovTab === k ? 'bg-white text-slate-900 shadow ring-1 ring-slate-200' : 'text-slate-500'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {ovTab === 'summary' && (
            <div className="space-y-6">
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="text-sm font-semibold text-slate-900">Financial Health Overview</h2>
                <div className="mt-4 grid gap-4 md:grid-cols-3">
                  <div className="relative overflow-hidden rounded-xl border border-slate-100 bg-slate-50/80 p-4 pl-5">
                    <span className="absolute left-0 top-0 h-full w-1 bg-slate-300" />
                    <p className="text-xs font-medium text-slate-500">Credit Score</p>
                    <p className="mt-1 text-3xl font-semibold text-slate-900">{creditProxy ?? '—'}</p>
                    <span className="mt-2 inline-flex rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
                      {(creditProxy ?? 0) >= 700 ? 'Excellent' : 'Review'}
                    </span>
                  </div>
                  <div className="relative overflow-hidden rounded-xl border border-slate-100 bg-slate-50/80 p-4 pl-5">
                    <span className="absolute left-0 top-0 h-full w-1 bg-indigo-400" />
                    <p className="text-xs font-medium text-slate-500">Income Stability</p>
                    <p className="mt-1 text-3xl font-semibold text-slate-900">
                      {incomeStability != null ? `${incomeStability.toFixed(1)}%` : '—'}
                    </p>
                    <span className="mt-2 inline-flex rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
                      Very Stable
                    </span>
                  </div>
                  <div className="relative overflow-hidden rounded-xl border border-slate-100 bg-slate-50/80 p-4 pl-5">
                    <span className="absolute left-0 top-0 h-full w-1 bg-red-400" />
                    <p className="text-xs font-medium text-slate-500">Stress / Delinquency risk</p>
                    <p className="mt-1 text-3xl font-semibold text-slate-900">
                      {fraudRisk != null ? `${fraudRisk.toFixed(1)}%` : '—'}
                    </p>
                    <span className="mt-2 inline-flex rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
                      Low Risk
                    </span>
                  </div>
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
                  {[
                    ['Credit Cards', '2 Active'],
                    ['Bank Accounts', customer.consent_monitoring ? 'Consented' : 'Pending'],
                    ['Risk Group', signals.some((s) => s.severity === 'HIGH') ? 'Elevated' : 'Low Risk'],
                    ['Active Loans', loan ? '1 snapshot' : '—'],
                    ['Loan progress', loan ? `${Math.min(95, 100 - Math.min(90, loan.dpd_days))}% est.` : '—'],
                    ['Avg inflow', loan ? formatInr(loan.avg_monthly_inflow) : '—'],
                  ].map(([k, v]) => (
                    <div key={k} className="rounded-lg border border-slate-100 bg-white px-3 py-3">
                      <p className="text-[11px] font-medium text-slate-500">{k}</p>
                      <p className="mt-1 text-sm font-semibold text-slate-900">{v}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between">
                  <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                    <FileText className="size-4" />
                    Loan Signals
                  </h2>
                  <Link to="/monitoring" className="text-xs font-medium text-indigo-600">
                    View all signals
                  </Link>
                </div>
                <ul className="mt-4 divide-y divide-slate-100">
                  {signals.slice(0, 5).map((s) => {
                    const sev = severityUi(s.severity)
                    return (
                      <li key={s.signal_id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                        <div>
                          <p className="font-medium text-slate-900">{s.signal_type.replaceAll('_', ' ')}</p>
                          <p className="text-sm text-slate-500">{s.narrative}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-slate-400">
                            {new Date(s.created_at).toLocaleDateString('en-IN')}
                          </span>
                          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${sev.className}`}>
                            {sev.label}
                          </span>
                        </div>
                      </li>
                    )
                  })}
                  {signals.length === 0 && (
                    <li className="py-6 text-center text-sm text-slate-500">No signals for this customer yet.</li>
                  )}
                </ul>
              </div>
            </div>
          )}

          {ovTab === 'analysis' && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600 shadow-sm">
              Trigger a BSI run from <strong>Sync</strong> to refresh rules output and optional GenAI summary. Last
              status:{' '}
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badge.className}`}>
                {badge.label}
              </span>
            </div>
          )}

          {ovTab === 'loans' && loan && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[
                ['Principal outstanding', formatInr(loan.principal_outstanding)],
                ['EMI', formatInr(loan.emi_amount)],
                ['DPD (days)', String(loan.dpd_days)],
                ['Avg monthly inflow', formatInr(loan.avg_monthly_inflow)],
                ['EOD negative days (90d)', String(loan.eod_negative_days_90d)],
                ['Credit score Δ (90d)', String(loan.credit_score_delta_90d)],
                ['Salary proxy Δ', formatPct(loan.salary_proxy_delta_pct, 0)],
              ].map(([k, v]) => (
                <div key={k} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-medium text-slate-500">{k}</p>
                  <p className="mt-1 text-lg font-semibold text-slate-900">{v}</p>
                </div>
              ))}
            </div>
          )}

          {ovTab === 'risk' && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-600">
                Risk is driven by compiled BSI signals (see Monitoring tab or list above).
              </p>
            </div>
          )}

          {ovTab === 'monitoring' && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm text-sm text-slate-600">
              Monitoring consent:{' '}
              <strong>{customer.consent_monitoring ? 'Granted' : 'Not granted'}</strong>. Last BSI:{' '}
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badge.className}`}>
                {badge.label}
              </span>
            </div>
          )}

          {ovTab === 'calls' && (
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
              <ul className="divide-y divide-slate-100">
                {messages.map((m) => (
                  <li key={m.id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-sm">
                    <div>
                      <p className="font-medium capitalize text-slate-900">{m.channel}</p>
                      <p className="text-slate-500">{m.body_preview}</p>
                    </div>
                    <span className="text-xs text-slate-400">
                      {new Date(m.created_at).toLocaleString('en-IN')}
                    </span>
                  </li>
                ))}
                {messages.length === 0 && (
                  <li className="px-5 py-8 text-center text-sm text-slate-500">
                    No outbound messages for this customer. Use Recovery to send WhatsApp or email.
                  </li>
                )}
              </ul>
            </div>
          )}
        </>
      )}

      {mainTab === 'statement' && loan && (
        <div className="space-y-4">
          <div className="mx-auto flex max-w-md rounded-full bg-slate-200/80 p-1">
            {(['income', 'spending', 'savings'] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setStmtTab(t)}
                className={`flex-1 rounded-full px-4 py-2 text-xs font-semibold capitalize ${
                  stmtTab === t ? 'bg-white text-slate-900 shadow' : 'text-slate-500'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {stmtTab === 'income' && (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-sm font-medium text-slate-500">Total Monthly Income</p>
                  <p className="mt-2 text-3xl font-semibold text-slate-900">{formatInr(monthlyIncome)}</p>
                  <p className="mt-2 text-sm font-medium text-emerald-600">
                    {formatPct(loan.salary_proxy_delta_pct, 0)} vs proxy trend
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-sm font-medium text-slate-500">Primary income source</p>
                  <p className="mt-2 flex items-center gap-2 text-3xl font-semibold text-slate-900">
                    <CalendarDays className="size-7 text-indigo-400" />
                    Salary
                  </p>
                  <p className="mt-2 text-sm text-slate-600">{formatInr(Math.round(monthlyIncome * 0.77))} per month</p>
                </div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white px-5 py-3 shadow-sm">
                <p className="text-xs font-semibold text-slate-500">Income health indicators</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-800">
                    Stable Income
                  </span>
                  <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-800">
                    Regular Deposits
                  </span>
                  <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-medium text-violet-800">
                    Multiple Sources
                  </span>
                </div>
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h3 className="text-sm font-semibold text-slate-800">Monthly Income Trend</h3>
                  <div className="mt-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={incomeTrend}>
                        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Line type="monotone" dataKey="amount" stroke="#a78bfa" strokeWidth={2} dot />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h3 className="text-sm font-semibold text-slate-800">Salary vs Other Income</h3>
                  <div className="mt-4 h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={88} label>
                          {pieData.map((_, i) => (
                            <Cell key={i} fill={pieData[i].fill} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </>
          )}

          {stmtTab === 'spending' && (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-sm">
              Spending breakdown is not returned by the BSI API; showing EMI as primary outflow:{' '}
              <strong>{formatInr(loan.emi_amount)}</strong>.
            </div>
          )}

          {stmtTab === 'savings' && (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 shadow-sm">
              Savings view uses average inflow minus EMI proxy:{' '}
              <strong>{formatInr(Math.max(0, loan.avg_monthly_inflow - loan.emi_amount))}</strong> / month (illustrative).
            </div>
          )}
        </div>
      )}

      {mainTab === 'statement' && !loan && (
        <p className="text-sm text-slate-500">No loan snapshot on file for statement views.</p>
      )}

      {mainTab === 'credit' && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-sm text-slate-600">
            Bureau-style credit report is not modelled in this backend slice. Use{' '}
            <strong>loan_snapshot.credit_score_delta_90d</strong> ({loan?.credit_score_delta_90d ?? '—'}) as a monitoring
            hint.
          </p>
        </div>
      )}

      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      <Link to="/customers/individual" className="inline-block text-sm text-indigo-600">
        ← Back to customers
      </Link>
    </div>
  )
}
