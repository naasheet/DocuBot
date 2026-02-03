'use client'

import { useMemo, useState } from 'react'
import { useRepos } from '../../lib/hooks/useRepos'
import Skeleton from '../../components/ui/Skeleton'

export default function DocsIndexPage() {
  const { repos, loading, error } = useRepos()
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return repos
    return repos.filter((repo: any) => {
      const name = (repo.full_name || repo.name || '').toLowerCase()
      const desc = (repo.description || '').toLowerCase()
      return name.includes(q) || desc.includes(q)
    })
  }, [repos, query])

  return (
    <div className="px-6 py-10 space-y-6 text-white">
      <div>
        <h1 className="text-3xl font-bold font-display">Docs Library</h1>
        <p className="text-sm text-white/60">
          Pick a repository to view README or API docs.
        </p>
      </div>

      <input
        type="text"
        placeholder="Search repositories..."
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        className="w-full max-w-md rounded-xl border border-white/10 bg-slate-950/40 px-4 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
      />

      {error && <div className="text-sm text-red-300">{error}</div>}
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
          {filtered.map((repo: any) => (
            <a
              key={repo.id || repo.full_name}
              href={`/docs/${repo.id}`}
              className="glass rounded-2xl p-4 space-y-2 transition hover:border-emerald-300/40"
            >
              <div className="text-sm font-semibold">{repo.full_name || repo.name}</div>
              {repo.description && <div className="text-xs text-white/60">{repo.description}</div>}
              <div className="text-xs text-white/50">View docs</div>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}
