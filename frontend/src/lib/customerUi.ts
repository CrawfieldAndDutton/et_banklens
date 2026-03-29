export function bsiStatusBadge(last: string | null | undefined): { label: string; className: string } {
  if (!last)
    return {
      label: 'Awaiting Data',
      className: 'bg-sky-100 text-sky-800',
    }
  if (last === 'INITIATED' || last === 'IN_PROGRESS')
    return { label: 'Under Review', className: 'bg-blue-100 text-blue-800' }
  if (last === 'COMPLETED')
    return { label: 'Data Received', className: 'bg-cyan-100 text-cyan-900' }
  if (last === 'FAILED') return { label: 'Rejected', className: 'bg-red-100 text-red-800' }
  return { label: last, className: 'bg-slate-100 text-slate-700' }
}

export function severityUi(sev: string): { label: string; className: string } {
  const s = sev.toUpperCase()
  if (s === 'HIGH') return { label: 'Critical', className: 'bg-red-100 text-red-800' }
  if (s === 'MEDIUM') return { label: 'Attention', className: 'bg-amber-100 text-amber-900' }
  return { label: 'Low', className: 'bg-emerald-100 text-emerald-800' }
}
