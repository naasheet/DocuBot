'use client'

import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'next/navigation'
import { api } from '../../../lib/api'
import Spinner from '../../../components/ui/Spinner'
import Skeleton from '../../../components/ui/Skeleton'
import { useTaskStore } from '../../../lib/store/taskStore'

type FileNode = {
  name: string
  path: string
  type: 'file' | 'dir'
  children?: FileNode[]
}

export default function RepoDetailPage() {
  const params = useParams()
  const repoId = Number(params?.id)
  const [repo, setRepo] = useState<any | null>(null)
  const [tree, setTree] = useState<FileNode | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const addTask = useTaskStore((state) => state.addTask)

  useEffect(() => {
    if (!repoId) return
    let isMounted = true
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [repoRes, treeRes] = await Promise.all([
          api.get(`/repos/${repoId}`),
          api.get(`/repos/${repoId}/tree`),
        ])
        if (isMounted) {
          setRepo(repoRes.data)
          setTree(treeRes.data)
        }
      } catch (err: any) {
        if (isMounted) setError(err?.message || 'Failed to load repository')
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    load()
    return () => {
      isMounted = false
    }
  }, [repoId])

  const handleAnalyze = async () => {
    setActionMessage(null)
    try {
      const res = await api.post(`/repos/${repoId}/analyze`)
      setActionMessage(`Analysis queued (task ${res.data?.task_id || 'unknown'})`)
      if (res.data?.task_id) {
        addTask({
          id: res.data.task_id,
          type: 'analysis',
          repoId,
          label: 'Repository analysis',
          status: 'queued',
          createdAt: Date.now(),
        })
      }
    } catch (err: any) {
      setActionMessage(err?.message || 'Failed to start analysis')
    }
  }

  const handleGenerateDocs = async (docType: string) => {
    setActionMessage(null)
    try {
      const res = await api.post('/docs/generate', { repo_id: repoId, doc_type: docType })
      setActionMessage(`Docs queued (task ${res.data?.task_id || 'unknown'})`)
      if (res.data?.task_id) {
        addTask({
          id: res.data.task_id,
          type: 'docs',
          repoId,
          label: docType === 'readme' ? 'Generate README' : 'Generate API Docs',
          status: 'queued',
          createdAt: Date.now(),
        })
      }
    } catch (err: any) {
      setActionMessage(err?.message || 'Failed to generate docs')
    }
  }

  if (loading) {
    return (
      <div className="p-8 space-y-4">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (error) {
    return <div className="p-8 text-sm text-red-300">{error}</div>
  }

  return (
    <div className="px-6 py-10 space-y-6 text-white">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold font-display">{repo?.full_name || repo?.name}</h1>
          {repo?.description && <p className="text-sm text-white/60">{repo.description}</p>}
          <div className="mt-2 text-xs text-white/50">ID: {repo?.id}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleAnalyze}
            className="rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900"
          >
            Analyze
          </button>
          <button
            onClick={() => handleGenerateDocs('readme')}
            className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80"
          >
            Generate README
          </button>
          <button
            onClick={() => handleGenerateDocs('api')}
            className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80"
          >
            Generate API Docs
          </button>
          <a
            href={`/docs/${repoId}`}
            className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80"
          >
            Open Docs
          </a>
          <a
            href={`/chat?repoId=${repoId}`}
            className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80"
          >
            Open Chat
          </a>
        </div>
      </div>

      {actionMessage && (
        <div className="flex items-center gap-2 text-sm text-emerald-300">
          <Spinner size={16} />
          {actionMessage}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass rounded-2xl p-4">
          <h2 className="text-lg font-semibold mb-3">Metadata</h2>
          <dl className="text-sm text-white/70 space-y-2">
            <div>
              <dt className="font-medium text-white/50">GitHub ID</dt>
              <dd>{repo?.github_id ?? '-'}</dd>
            </div>
            <div>
              <dt className="font-medium text-white/50">URL</dt>
              <dd className="break-all">{repo?.url || '-'}</dd>
            </div>
            <div>
              <dt className="font-medium text-white/50">Active</dt>
              <dd>{repo?.is_active ? 'Yes' : 'No'}</dd>
            </div>
          </dl>
        </div>
        <div className="glass rounded-2xl p-4">
          <h2 className="text-lg font-semibold mb-3">Actions</h2>
          <p className="text-sm text-white/60">
            Run an analysis to parse code and enable fast Q&amp;A. Generate docs to create
            README or API reference pages.
          </p>
        </div>
      </div>

      <div className="glass rounded-2xl p-4">
        <h2 className="text-lg font-semibold mb-3">File Tree</h2>
        {tree ? <TreeView node={tree} /> : <p className="text-sm text-white/60">No tree yet.</p>}
      </div>
    </div>
  )
}

function TreeView({ node, depth = 0 }: { node: FileNode; depth?: number }) {
  const indent = useMemo(() => ({ marginLeft: depth * 12 }), [depth])
  if (!node) return null
  const children = node.children || []

  return (
    <div className="space-y-1">
      {node.name && (
        <div style={indent} className="text-sm text-white/80">
          {node.type === 'dir' ? '[DIR]' : '[FILE]'} {node.name}
        </div>
      )}
      {children.map((child) => (
        <TreeView key={`${child.path}-${child.name}`} node={child} depth={depth + 1} />
      ))}
    </div>
  )
}
