import { Sparkles } from 'lucide-react'

export function AIAssistantFab() {
  return (
    <button
      type="button"
      className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-[#1a1f2e] px-5 py-3 text-sm font-medium text-white shadow-lg shadow-slate-900/20 transition hover:bg-[#252b3d]"
    >
      <Sparkles className="size-4 shrink-0 text-amber-300" />
      AI Assistant
    </button>
  )
}
