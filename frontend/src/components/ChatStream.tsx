'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type StreamEvent = {
  event: string
  data: string
}

function parseEvent(raw: string): StreamEvent {
  const lines = raw.split('\n')
  let event = 'message'
  const dataLines: string[] = []
  for (const line of lines) {
    if (line.startsWith('event:')) {
      event = line.replace('event:', '').trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.replace('data:', '').trimEnd())
    }
  }
  return { event, data: dataLines.join('\n') }
}

export default function ChatStream() {
  const searchParams = useSearchParams()
  const [repoId, setRepoId] = useState('')
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const paramValue = searchParams.get('repoId')
    if (paramValue && !repoId) {
      setRepoId(paramValue)
    }
  }, [searchParams, repoId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setAnswer('')
    setError(null)
    setIsLoading(true)

    try {
      const token = localStorage.getItem('token') || ''
      const res = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          repo_id: Number(repoId),
          query,
          session_id: sessionId,
        }),
      })

      if (!res.ok || !res.body) {
        throw new Error(`Request failed (${res.status})`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''
        for (const part of parts) {
          const evt = parseEvent(part)
          if (evt.event === 'meta') {
            try {
              const meta = JSON.parse(evt.data)
              if (meta.session_id) {
                setSessionId(meta.session_id)
              }
            } catch {
              // ignore malformed meta
            }
          } else if (evt.event === 'error') {
            setError(evt.data)
          } else if (evt.event === 'done') {
            setIsLoading(false)
          } else if (evt.data) {
            setAnswer((prev) => prev + evt.data)
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Ask the Repo</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="number"
          placeholder="Repository ID"
          value={repoId}
          onChange={(e) => setRepoId(e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
          required
        />
        <textarea
          placeholder="Ask a question about the code..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-2xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
          rows={4}
          required
        />
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-900/30 border-t-slate-900" />
              Thinking...
            </span>
          ) : (
            'Send'
          )}
        </button>
      </form>
      {error && <div className="text-red-300">{error}</div>}
      <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-3 whitespace-pre-wrap">
        {answer || 'Your streaming answer will appear here.'}
      </div>
    </div>
  )
}
