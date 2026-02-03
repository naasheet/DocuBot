'use client'

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-8 text-white">
      <div className="max-w-lg rounded-2xl border border-white/10 bg-slate-950/80 p-6 text-center space-y-3">
        <h2 className="text-2xl font-bold font-display">Something went wrong</h2>
        <p className="text-sm text-white/60">
          A server error occurred. Please try again or return later.
        </p>
        <div className="text-xs text-white/50">{error?.message}</div>
        <button
          onClick={reset}
          className="rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900"
        >
          Try again
        </button>
      </div>
    </div>
  )
}
