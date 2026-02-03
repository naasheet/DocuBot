'use client'

import { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'

import { useRepos } from '../../lib/hooks/useRepos'
import AddRepoModal from '../../components/AddRepoModal'
import Skeleton from '../../components/ui/Skeleton'
import { api } from '../../lib/api'
import ConnectGitHubLink from '../../components/ConnectGitHubLink'

export default function ReposPage() {
  const { repos, loading, error } = useRepos()
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [loadingRepo, setLoadingRepo] = useState<string | number | null>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return repos
    return repos.filter((repo: any) => {
      const name = (repo.full_name || repo.name || '').toLowerCase()
      const desc = (repo.description || '').toLowerCase()
      return name.includes(q) || desc.includes(q)
    })
  }, [repos, query])

  const handleOpenRepo = async (repo: any) => {
    const repoUrl = repo.html_url || repo.url
    if (!repoUrl) {
      setActionError('Repository URL not found')
      return
    }
    setActionError(null)
    setLoadingRepo(repo.id || repo.full_name || repo.name)
    try {
      const res = await api.post('/repos', { url: repoUrl })
      const repoId = res.data?.id
      if (repoId) {
        router.push(`/repos/${repoId}`)
      } else {
        setActionError('Repository not found')
      }
    } catch (err: any) {
      setActionError(err?.message || 'Failed to add repository')
    } finally {
      setLoadingRepo(null)
    }
  }

  return (
    <div className="px-6 py-10 space-y-6 text-white">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold font-display">Repositories</h1>
          <p className="text-sm text-white/60">Browse and manage connected repos.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <ConnectGitHubLink className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80 transition hover:text-white" />
          <button
            className="rounded-full bg-emerald-300 px-5 py-2 text-sm font-semibold text-slate-900 transition hover:-translate-y-0.5 hover:bg-emerald-200"
            onClick={() => setIsModalOpen(true)}
          >
            Add Repo
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="Search repositories..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="w-full max-w-md rounded-xl border border-white/10 bg-slate-950/40 px-4 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
        />
      </div>

      {error && <div className="text-sm text-red-300">{error}</div>}
      {actionError && <div className="text-sm text-red-300">{actionError}</div>}
      {loading && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-24 w-full" />
          ))}
        </div>
      )}
      {!loading && filtered.length === 0 && (
        <div className="text-sm text-white/60">No repositories found.</div>
      )}

      {!loading && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((repo: any) => {
            const loadingKey = repo.id || repo.full_name || repo.name
            const isBusy = loadingRepo === loadingKey
            return (
              <button
                key={repo.id || repo.full_name}
                type="button"
                onClick={() => handleOpenRepo(repo)}
                className="glass rounded-2xl p-4 space-y-2 text-left transition hover:border-emerald-300/40"
              >
                <div className="text-sm font-semibold">{repo.full_name || repo.name}</div>
                {repo.description && (
                  <div className="text-xs text-white/60">{repo.description}</div>
                )}
                <div className="flex items-center gap-2 text-xs text-white/50">
                  <span>ID: {repo.id || '-'}</span>
                  <span className="text-white/30">|</span>
                  <span>{repo.private ? 'Private' : 'Public'}</span>
                </div>
                <div className="text-xs text-emerald-200">
                  {isBusy ? 'Adding repo...' : 'Open workspace'}
                </div>
              </button>
            )
          })}
        </div>
      )}

      <AddRepoModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => setIsModalOpen(false)}
      />
    </div>
  )
}
