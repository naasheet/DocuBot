'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

type Props = {
  content: string
}

export default function MarkdownViewer({ content }: Props) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedCode(text)
      setTimeout(() => setCopiedCode(null), 1500)
    } catch {
      setCopiedCode(null)
    }
  }

  return (
    <div className="prose prose-invert prose-slate max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          code({ inline, className, children }) {
            const raw = String(children || '').replace(/\n$/, '')
            if (inline) {
              return <code className={className}>{children}</code>
            }
            return (
              <div className="relative">
                <button
                  onClick={() => handleCopy(raw)}
                  className="absolute right-2 top-2 rounded bg-white/10 px-2 py-1 text-xs text-white hover:bg-white/20"
                  type="button"
                >
                  {copiedCode === raw ? 'Copied' : 'Copy'}
                </button>
                <pre>
                  <code className={className}>{children}</code>
                </pre>
              </div>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
