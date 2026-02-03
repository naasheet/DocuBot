'use client'

import { useEffect, useState } from 'react'
import ChatStream from '../../components/ChatStream'
import { useRepos } from '../../lib/hooks/useRepos'
import { useAuthStore } from '../../lib/store/authStore'
import Skeleton from '../../components/ui/Skeleton'
import ConnectGitHubLink from '../../components/ConnectGitHubLink'

export default function DashboardPage() {
  const { repos, loading, error } = useRepos()
  const user = useAuthStore((state) => state.user)
  const updateName = useAuthStore((state) => state.updateName)
  const [firstName, setFirstName] = useState('')
  const [nameError, setNameError] = useState<string | null>(null)
  const [savingName, setSavingName] = useState(false)
  const recentRepos = (repos || []).slice(0, 5)

  useEffect(() => {
    if (user?.full_name) {
      setFirstName(user.full_name)
    }
  }, [user?.full_name])

  const handleNameSave = async (event: React.FormEvent) => {
    event.preventDefault()
    const name = firstName.trim()
    if (!name) {
      setNameError('First name is required')
      return
    }
    setNameError(null)
    setSavingName(true)
    try {
      await updateName(name)
    } catch (err: any) {
      setNameError(err?.message || 'Failed to update name')
    } finally {
      setSavingName(false)
    }
  }

  return (
    <div className="px-6 py-10 space-y-6 text-white">
      <div>
        <h1 className="text-3xl font-bold mb-2 font-display">Dashboard</h1>
        <p className="text-white/70">
          Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="glass rounded-2xl p-4">
          <div className="text-sm text-white/60">Repositories</div>
          {loading ? (
            <Skeleton className="mt-2 h-7 w-16" />
          ) : (
            <div className="text-2xl font-semibold">{repos.length}</div>
          )}
        </div>
        <div className="glass rounded-2xl p-4">
          <div className="text-sm text-white/60">Docs Generated</div>
          <div className="text-2xl font-semibold">0</div>
          <div className="text-xs text-white/50">No docs yet</div>
        </div>
        <div className="glass rounded-2xl p-4">
          <div className="text-sm text-white/60">Last Activity</div>
          <div className="text-2xl font-semibold">-</div>
          <div className="text-xs text-white/50">Waiting for first run</div>
        </div>
      </div>

      <div className="glass rounded-2xl p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Your profile</h2>
            <p className="text-sm text-white/60">Set your first name for a better experience.</p>
          </div>
          <ConnectGitHubLink className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80" />
        </div>
        <form onSubmit={handleNameSave} className="mt-4 flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="First name"
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
            className="w-full max-w-sm rounded-xl border border-white/10 bg-slate-950/40 px-4 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
            required
          />
          <button
            type="submit"
            className="rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
            disabled={savingName}
          >
            {savingName ? 'Saving...' : 'Save name'}
          </button>
        </form>
        {nameError && <p className="mt-2 text-sm text-red-300">{nameError}</p>}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="glass rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent Repos</h2>
            <a href="/repos" className="text-sm text-emerald-300 hover:underline">
              View all
            </a>
          </div>
          {error && <p className="mt-2 text-sm text-red-300">{error}</p>}
          {loading && (
            <div className="mt-3 space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}
          {!loading && recentRepos.length === 0 && (
            <p className="mt-3 text-sm text-white/60">No repositories added yet.</p>
          )}
          <ul className="mt-3 space-y-2">
            {recentRepos.map((repo: any) => (
              <li key={repo.id || repo.full_name} className="rounded-xl border border-white/10 px-3 py-2">
                <div className="text-sm font-medium">{repo.full_name || repo.name}</div>
                {repo.description && <div className="text-xs text-white/60">{repo.description}</div>}
              </li>
            ))}
          </ul>
        </div>

        <div className="glass rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent Docs</h2>
            <span className="text-sm text-white/50">Coming soon</span>
          </div>
          <p className="mt-3 text-sm text-white/60">
            Generated docs will appear here once you analyze a repository.
          </p>
        </div>
      </div>

      <div className="glass rounded-2xl p-4">
        <h2 className="text-lg font-semibold mb-3">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <a href="/repos" className="rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900">
            Add Repository
          </a>
          <a href="/repos" className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80">
            View Repos
          </a>
          <ConnectGitHubLink className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80" />
        </div>
      </div>

      <ChatStream />
    </div>
  )
}
