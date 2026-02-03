'use client'

import MarkdownViewer from '../MarkdownViewer'

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

type Props = {
  messages: Message[]
}

export default function MessageList({ messages }: Props) {
  if (messages.length === 0) {
    return <div className="text-sm text-white/60">No messages yet.</div>
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`rounded-2xl border border-white/10 p-4 ${
            message.role === 'user' ? 'bg-white/5' : 'bg-slate-950/40'
          }`}
        >
          <div className="mb-2 text-xs uppercase tracking-wide text-white/40">
            {message.role === 'user' ? 'You' : 'Assistant'}
          </div>
          {message.role === 'assistant' ? (
            <MarkdownViewer content={message.content} />
          ) : (
            <p className="text-sm whitespace-pre-wrap text-white/90">{message.content}</p>
          )}
        </div>
      ))}
    </div>
  )
}
