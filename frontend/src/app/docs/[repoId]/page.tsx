'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { api } from '../../../lib/api'
import MarkdownViewer from '../../../components/MarkdownViewer'
import Skeleton from '../../../components/ui/Skeleton'
import Spinner from '../../../components/ui/Spinner'

type DocType = 'readme' | 'api'

export default function DocumentationPage() {
  const params = useParams()
  const repoId = Number(params?.repoId)
  const [docType, setDocType] = useState<DocType>('readme')
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!repoId) return
    let isMounted = true
    const fetchDoc = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await api.get(`/docs/${repoId}`, { params: { doc_type: docType } })
        if (isMounted) setContent(res.data?.content || '')
      } catch (err: any) {
        if (isMounted) setError(err?.message || 'Failed to load documentation')
      } finally {
        if (isMounted) setLoading(false)
      }
    }
    fetchDoc()
    return () => {
      isMounted = false
    }
  }, [repoId, docType])

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `repo-${repoId}-${docType}.md`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="px-6 py-10 space-y-6 text-white">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold font-display">Documentation</h1>
          <p className="text-sm text-white/60">Repo ID: {repoId}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={docType}
            onChange={(event) => setDocType(event.target.value as DocType)}
            className="rounded-full border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white focus:border-emerald-300/40 focus:outline-none"
          >
            <option value="readme">README</option>
            <option value="api">API Docs</option>
          </select>
          <button
            onClick={handleDownload}
            className="rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
            disabled={!content}
          >
            Download
          </button>
        </div>
      </div>

      {loading && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-white/60">
            <Spinner size={16} />
            Loading documentation...
          </div>
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}
      {error && <div className="text-sm text-red-300">{error}</div>}
      {!loading && !error && content && (
        <div className="glass rounded-2xl p-6">
          <MarkdownViewer content={content} />
        </div>
      )}
      {!loading && !error && !content && (
        <div className="text-sm text-white/60">No documentation available yet.</div>
      )}
    </div>
  )
}
