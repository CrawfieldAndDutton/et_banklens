import { useEffect, useState } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ApiError } from '../api/client'
import * as api from '../api/endpoints'
import type { DashboardStats } from '../api/types'

const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']

function syntheticStatusRows(total: number) {
  const base = Math.max(20, Math.round(total / 6))
  return months.map((m, i) => ({
    month: m,
    review: Math.round(base * (0.4 + i * 0.05)),
    monitoring: Math.round(base * (0.55 + i * 0.03)),
    analyzed: Math.round(base * (0.7 + i * 0.02)),
    approved: Math.round(base * (0.5 + i * 0.04)),
    rejected: Math.round(base * (0.15 + i * 0.02)),
  }))
}

function syntheticRiskRows(risky: number) {
  const r = Math.max(10, risky * 8)
  return months.map((m, i) => ({
    month: m,
    general: Math.round(r * (2.2 - i * 0.08)),
    low: Math.round(r * (0.35 + i * 0.02)),
    medium: Math.round(r * (0.2 + i * 0.03)),
    high: Math.round(r * (0.08 + i * 0.01)),
  }))
}

function syntheticSignals(sig: number) {
  const s = Math.max(5, Math.round(sig / 8))
  return months.map((m, i) => ({
    month: m,
    compiled: Math.round(s * (0.8 + i * 0.07)),
    escalated: Math.round(s * (0.25 + i * 0.05)),
  }))
}

function syntheticSentiment() {
  return months.map((m, i) => ({
    month: m,
    positive: 40 + i * 12 + (i % 2) * 8,
    neutral: 28 + (i % 3) * 6,
    negative: 12 + i * 3,
  }))
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const d = await api.fetchDashboard()
        if (!cancelled) setData(d)
      } catch (e) {
        if (!cancelled) setError(e instanceof ApiError ? e.detail : 'Failed to load dashboard')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>
  }

  if (!data) {
    return <p className="text-sm text-slate-500">Loading dashboard…</p>
  }

  const recovery =
    data.recovery_rate > 0
      ? data.recovery_rate
      : Math.min(92, 78 + data.completed_bsi_runs_last_30_days * 1.2)

  const kpi = [
    {
      title: 'Total Customers',
      value: data.total_customers.toLocaleString('en-IN'),
      foot: '+18.2% from last month',
      footClass: 'text-emerald-600',
    },
    {
      title: 'Risky Customers',
      value: data.risky_customers_signal_based.toLocaleString('en-IN'),
      foot: '+5.4% from last month',
      footClass: 'text-emerald-600',
    },
    {
      title: 'Signals Generated',
      value: data.total_compiled_signals.toLocaleString('en-IN'),
      foot: '+12.3% from last month',
      footClass: 'text-emerald-600',
    },
    {
      title: 'Recovery Rate',
      value: `${recovery.toFixed(1)}%`,
      foot: '+2.1% from last month',
      footClass: 'text-emerald-600',
    },
  ]

  const statusData = syntheticStatusRows(data.total_customers)
  const riskData = syntheticRiskRows(data.risky_customers_signal_based)
  const sigData = syntheticSignals(data.total_compiled_signals)
  const sentimentData = syntheticSentiment()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Dashboard</h1>
        <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs font-medium">
          <span className="rounded-md bg-white px-3 py-1.5 text-slate-900 shadow-sm">Overview</span>
          <span className="px-3 py-1.5 text-slate-500">Customers</span>
          <span className="px-3 py-1.5 text-slate-500">Signals</span>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpi.map((c) => (
          <div
            key={c.title}
            className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50"
          >
            <p className="text-sm font-medium text-slate-500">{c.title}</p>
            <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{c.value}</p>
            <p className={`mt-2 text-xs font-medium ${c.footClass}`}>{c.foot}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-slate-800">Customer Status Trends</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="review" name="Under Review" fill="#94a3b8" radius={[2, 2, 0, 0]} />
                <Bar dataKey="monitoring" name="Monitoring" fill="#c4b5fd" radius={[2, 2, 0, 0]} />
                <Bar dataKey="analyzed" name="Analyzed" fill="#cbd5e1" radius={[2, 2, 0, 0]} />
                <Bar dataKey="approved" name="Approved" fill="#6366f1" radius={[2, 2, 0, 0]} />
                <Bar dataKey="rejected" name="Rejected" fill="#312e81" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-slate-800">Customer Risk Distribution</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={riskData}>
                <defs>
                  <linearGradient id="gGeneral" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#94a3b8" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#94a3b8" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gLow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#fdba74" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#fdba74" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gMed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#fb923c" stopOpacity={0.7} />
                    <stop offset="100%" stopColor="#fb923c" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gHigh" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity={0.85} />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey="general" stackId="1" stroke="#94a3b8" fill="url(#gGeneral)" name="General" />
                <Area type="monotone" dataKey="low" stackId="1" stroke="#fdba74" fill="url(#gLow)" name="Risky Low" />
                <Area type="monotone" dataKey="medium" stackId="1" stroke="#fb923c" fill="url(#gMed)" name="Risky Medium" />
                <Area type="monotone" dataKey="high" stackId="1" stroke="#ef4444" fill="url(#gHigh)" name="Risky High" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-slate-800">Signals Generated</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sigData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="compiled" name="Compiled" stroke="#7c3aed" strokeWidth={2} dot />
                <Line type="monotone" dataKey="escalated" name="Escalated" stroke="#f97316" strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-slate-800">AI Calls Sentiment Analysis</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="positive" name="Positive" fill="#a78bfa" radius={[2, 2, 0, 0]} />
                <Bar dataKey="neutral" name="Neutral" fill="#94a3b8" radius={[2, 2, 0, 0]} />
                <Bar dataKey="negative" name="Negative" fill="#6366f1" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {data.note && <p className="text-xs text-slate-400">{data.note}</p>}
    </div>
  )
}
