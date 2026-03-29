import { Bell, Search } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export function TopBar() {
  const { me } = useAuth()
  const initials = me?.email
    ? me.email
        .split('@')[0]
        .slice(0, 2)
        .toUpperCase()
    : 'AD'

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-4 border-b border-slate-200/80 bg-white/90 px-6 backdrop-blur-md">
      <div className="relative max-w-md flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          placeholder="Search..."
          className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2 pl-10 pr-3 text-sm outline-none ring-indigo-500/30 placeholder:text-slate-400 focus:border-indigo-300 focus:bg-white focus:ring-2"
        />
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="relative rounded-lg p-2 text-slate-600 hover:bg-slate-100"
          aria-label="Notifications"
        >
          <Bell className="size-5" />
          <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-red-500 ring-2 ring-white" />
        </button>
        <div className="flex size-9 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-800">
          {initials}
        </div>
      </div>
    </header>
  )
}
