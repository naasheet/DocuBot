'use client'

import ChatUI from '../../components/chat/ChatUI'

export default function ChatPage() {
  return (
    <div className="px-6 py-10 space-y-6 text-white">
      <div>
        <h1 className="text-3xl font-bold font-display">Code Chat</h1>
        <p className="text-sm text-white/60">
          Ask questions about your repository. Answers include relevant code snippets.
        </p>
      </div>
      <div className="glass rounded-2xl p-6">
        <ChatUI />
      </div>
    </div>
  )
}
