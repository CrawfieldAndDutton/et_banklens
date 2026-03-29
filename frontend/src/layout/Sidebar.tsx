import {
  BarChart3,
  Bell,
  Briefcase,
  ChevronDown,
  ChevronLeft,
  Home,
  PanelLeftClose,
  Phone,
  Settings,
  Shield,
  Users,
} from 'lucide-react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useState } from 'react'

const navClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
    isActive ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-sidebar-hover hover:text-white'
  }`

export function Sidebar() {
  const { me } = useAuth()
  const loc = useLocation()
  const [customersOpen, setCustomersOpen] = useState(
    loc.pathname.startsWith('/customers'),
  )
  const [collapsed, setCollapsed] = useState(false)

  const initials = me?.email
    ? me.email
        .split('@')[0]
        .slice(0, 2)
        .toUpperCase()
    : 'AD'

  return (
    <aside
      className={`flex h-screen shrink-0 flex-col border-r border-white/5 bg-sidebar text-white transition-[width] duration-200 ${
        collapsed ? 'w-[72px]' : 'w-60'
      }`}
    >
      <div className="flex items-center justify-between gap-2 border-b border-white/5 px-3 py-4">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-amber-500/20 text-amber-400">
            <Shield className="size-5" />
          </div>
          {!collapsed && <span className="truncate font-semibold tracking-tight">BankLens</span>}
        </div>
        {!collapsed && (
          <button
            type="button"
            onClick={() => setCollapsed(true)}
            className="rounded-md p-1.5 text-slate-500 hover:bg-white/10 hover:text-white"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="size-4" />
          </button>
        )}
        {collapsed && (
          <button
            type="button"
            onClick={() => setCollapsed(false)}
            className="mx-auto rounded-md p-1.5 text-slate-500 hover:bg-white/10 hover:text-white"
            aria-label="Expand sidebar"
          >
            <ChevronLeft className="size-4 rotate-180" />
          </button>
        )}
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-2">
        <NavLink to="/dashboard" end className={navClass}>
          <Home className="size-[18px] shrink-0 opacity-80" />
          {!collapsed && 'Dashboard'}
        </NavLink>
        <NavLink to="/users" className={navClass}>
          <Users className="size-[18px] shrink-0 opacity-80" />
          {!collapsed && 'Users'}
        </NavLink>

        <div>
          <button
            type="button"
            onClick={() => !collapsed && setCustomersOpen((o) => !o)}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
              loc.pathname.startsWith('/customers')
                ? 'bg-white/10 text-white'
                : 'text-slate-400 hover:bg-sidebar-hover hover:text-white'
            }`}
          >
            <Briefcase className="size-[18px] shrink-0 opacity-80" />
            {!collapsed && (
              <>
                <span className="flex-1 text-left">Customers</span>
                <ChevronDown
                  className={`size-4 transition ${customersOpen ? 'rotate-0' : '-rotate-90'}`}
                />
              </>
            )}
          </button>
          {!collapsed && customersOpen && (
            <div className="ml-2 mt-0.5 space-y-0.5 border-l border-white/10 pl-2">
              <NavLink
                to="/customers/individual"
                className={({ isActive }) =>
                  `block rounded-md px-3 py-2 text-sm ${isActive ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`
                }
              >
                Individual
              </NavLink>
              <NavLink
                to="/customers/business"
                className={({ isActive }) =>
                  `block rounded-md px-3 py-2 text-sm ${isActive ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white'}`
                }
              >
                Business
              </NavLink>
            </div>
          )}
        </div>

        <NavLink to="/monitoring" className={navClass}>
          <BarChart3 className="size-[18px] shrink-0 opacity-80" />
          {!collapsed && 'Monitoring'}
        </NavLink>
        <NavLink to="/recovery" className={navClass}>
          <Phone className="size-[18px] shrink-0 opacity-80" />
          {!collapsed && 'Recovery'}
        </NavLink>
        <NavLink to="/notifications" className={navClass}>
          <Bell className="size-[18px] shrink-0 opacity-80" />
          {!collapsed && 'Notifications'}
        </NavLink>
        <NavLink to="/settings" className={navClass}>
          <Settings className="size-[18px] shrink-0 opacity-80" />
          {!collapsed && 'Settings'}
        </NavLink>
      </nav>

      <div className="border-t border-white/5 p-3">
        <div className="flex items-center gap-3 rounded-lg bg-white/5 px-2 py-2">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-indigo-500/30 text-xs font-semibold text-indigo-100">
            {initials}
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">Admin User</p>
              <p className="truncate text-xs text-slate-500">{me?.email ?? '—'}</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
