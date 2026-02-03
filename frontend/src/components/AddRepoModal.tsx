'use client'

import { useState } from 'react'
import { api } from '../lib/api'

type Props = {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

export default function AddRepoModal({ isOpen, onClose, onSuccess }: Props) {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)
    if (!url.trim()) {
      setError('GitHub URL is required')
      return
    }
    setIsLoading(true)
    try {
      await api.post('/repos', { url: url.trim() })
      setSuccess('Repository added')
      setUrl('')
      if (onSuccess) onSuccess()
    } catch (err: any) {
      setError(err?.message || 'Failed to add repository')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950/90 p-6 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Add Repository</h3>
          <button onClick={onClose} className="text-sm text-white/60 hover:text-white">
            Close
          </button>
        </div>
        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-white/80">GitHub URL</label>
            <input
              type="text"
              placeholder="https://github.com/owner/repo"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
            />
          </div>
          {error && <div className="text-sm text-red-300">{error}</div>}
          {success && <div className="text-sm text-emerald-300">{success}</div>}
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isLoading}
              className="rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
            >
              {isLoading ? 'Adding...' : 'Add Repo'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/80"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
