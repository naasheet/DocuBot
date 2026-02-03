'use client'

import { useState } from 'react'

type Props = {
  onSend: (text: string) => Promise<void>
  isLoading?: boolean
}

export default function MessageInput({ onSend, isLoading }: Props) {
  const [value, setValue] = useState('')

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = value.trim()
    if (!trimmed) return
    await onSend(trimmed)
    setValue('')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Ask a question about the code..."
        className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
        rows={3}
        required
      />
      <div className="flex items-center justify-between">
        <div className="text-xs text-white/50">
          Tip: include file names or function names for better results.
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-900/30 border-t-slate-900" />
              Sending...
            </span>
          ) : (
            'Send'
          )}
        </button>
      </div>
    </form>
  )
}
