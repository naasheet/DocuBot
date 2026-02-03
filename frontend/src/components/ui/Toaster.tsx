'use client'

import { useToastStore } from '../../lib/store/toastStore'

export default function Toaster() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed right-4 top-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`rounded-2xl border px-4 py-2 text-sm shadow ${
            toast.type === 'error'
              ? 'border-red-500/30 bg-red-500/10 text-red-200'
              : toast.type === 'success'
              ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-100'
              : 'border-white/10 bg-slate-950/80 text-white/80'
          }`}
        >
          <div className="flex items-center justify-between gap-3">
            <span>{toast.message}</span>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-xs text-white/50 hover:text-white"
            >
              Close
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
