import { Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'

/** Backend has no user-management API; static demo rows aligned with seeded roles. */
const DEMO_USERS = [
  {
    name: 'Vikram Mehta',
    email: 'vikram.mehta@example.com',
    role: 'Admin',
    status: 'Active',
  },
  {
    name: 'Priya Singh',
    email: 'priya.singh@example.com',
    role: 'Underwriter',
    status: 'Active',
  },
  {
    name: 'Rahul Kapoor',
    email: 'rahul.kapoor@example.com',
    role: 'Monitor',
    status: 'Active',
  },
  {
    name: 'Aisha Patel',
    email: 'aisha.patel@example.com',
    role: 'Recovery Agent',
    status: 'Inactive',
  },
  {
    name: 'Sanjay Kumar',
    email: 'sanjay.kumar@example.com',
    role: 'Underwriter',
    status: 'Active',
  },
]

export function UsersPage() {
  const [tab, setTab] = useState<'users' | 'roles'>('users')

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Role &amp; User Management</h1>
          <p className="mt-1 text-sm text-slate-500">
            Demo listing — the API does not expose tenant users yet. Live auth uses{' '}
            <code className="rounded bg-slate-100 px-1 text-xs">/api/v1/auth/login</code>.
          </p>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-lg bg-[#1a233a] px-4 py-2.5 text-sm font-medium text-white"
        >
          <Plus className="size-4" />
          New User
        </button>
      </div>

      <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-1">
        <button
          type="button"
          onClick={() => setTab('users')}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            tab === 'users' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
          }`}
        >
          Users
        </button>
        <button
          type="button"
          onClick={() => setTab('roles')}
          className={`rounded-md px-4 py-2 text-sm font-medium ${
            tab === 'roles' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
          }`}
        >
          Roles
        </button>
      </div>

      {tab === 'roles' ? (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-sm text-slate-600 shadow-sm">
          Role definitions mirror backend <code className="rounded bg-slate-50 px-1">UserRole</code>: admin,
          analyst, compliance — with permissions in{' '}
          <code className="rounded bg-slate-50 px-1">domain/permissions.py</code>.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">Email</th>
                <th className="px-5 py-3">Role</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_USERS.map((u) => (
                <tr key={u.email} className="border-b border-slate-50 last:border-0">
                  <td className="px-5 py-3.5 font-medium text-slate-900">{u.name}</td>
                  <td className="px-5 py-3.5 text-slate-600">{u.email}</td>
                  <td className="px-5 py-3.5 text-slate-700">{u.role}</td>
                  <td className="px-5 py-3.5">
                    <span className="text-emerald-600">{u.status}</span>
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button type="button" className="mr-2 inline-flex rounded p-1.5 text-slate-500 hover:bg-slate-100">
                      <Pencil className="size-4" />
                    </button>
                    <button type="button" className="inline-flex rounded p-1.5 text-slate-500 hover:bg-slate-100">
                      <Trash2 className="size-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
