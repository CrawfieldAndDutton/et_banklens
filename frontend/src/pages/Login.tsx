import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Shield } from 'lucide-react'

export function LoginPage() {
  const { token, login, loading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  if (token && !loading) {
    return <Navigate to="/dashboard" replace />
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr(null)
    setPending(true)
    try {
      await login(email.trim(), password)
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : 'Sign-in failed')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#1a1f2e] px-4">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white p-8 shadow-2xl">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <div className="flex size-14 items-center justify-center rounded-xl bg-amber-500/15 text-amber-500">
            <Shield className="size-8" />
          </div>
          <h1 className="text-2xl font-semibold text-slate-900">BankLens</h1>
          <p className="text-sm text-slate-500">Sign in with your workspace account</p>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Email</label>
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none ring-indigo-500/20 focus:border-indigo-400 focus:ring-2"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Password</label>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none ring-indigo-500/20 focus:border-indigo-400 focus:ring-2"
            />
          </div>
          {err && <p className="text-sm text-red-600">{err}</p>}
          <button
            type="submit"
            disabled={pending || loading}
            className="w-full rounded-lg bg-[#1e1b4b] py-2.5 text-sm font-medium text-white transition hover:bg-indigo-950 disabled:opacity-60"
          >
            {pending || loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="mt-6 text-center text-xs text-slate-400">
          Use credentials from your backend <code className="rounded bg-slate-100 px-1">.env</code>{' '}
          (e.g. <code className="rounded bg-slate-100 px-1">DEMO_USER_EMAIL</code>).
        </p>
      </div>
    </div>
  )
}
