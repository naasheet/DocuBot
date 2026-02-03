'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { api } from '../../lib/api'
import MessageList from './MessageList'
import MessageInput from './MessageInput'

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export default function ChatUI() {
  const searchParams = useSearchParams()
  const [repoId, setRepoId] = useState('')
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const paramValue = searchParams.get('repoId')
    if (paramValue && !repoId) {
      setRepoId(paramValue)
    }
  }, [searchParams, repoId])

  const sendMessage = async (text: string) => {
    if (!repoId) {
      setError('Repository ID is required')
      return
    }
    setError(null)
    const userMessage: Message = {
      id: `${Date.now()}-user`,
      role: 'user',
      content: text,
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const res = await api.post('/chat', {
        repo_id: Number(repoId),
        query: text,
        session_id: sessionId,
      })
      if (res.data?.session_id) {
        setSessionId(res.data.session_id)
      }
      const assistantMessage: Message = {
        id: `${Date.now()}-assistant`,
        role: 'assistant',
        content: res.data?.answer || '',
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err: any) {
      setError(err?.message || 'Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="number"
          placeholder="Repository ID"
          value={repoId}
          onChange={(event) => setRepoId(event.target.value)}
          className="w-full max-w-xs rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
        />
        {sessionId && <span className="text-xs text-white/60">Session {sessionId}</span>}
      </div>
      {error && <div className="text-sm text-red-300">{error}</div>}
      <MessageList messages={messages} />
      <MessageInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  )
}
