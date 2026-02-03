'use client'

import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { useTaskStore, TaskItem } from '../lib/store/taskStore'
import { useToastStore } from '../lib/store/toastStore'

const ACTIVE_STATES = new Set(['queued', 'running'])

function mapState(state?: string): TaskItem['status'] {
  switch ((state || '').toUpperCase()) {
    case 'SUCCESS':
      return 'completed'
    case 'FAILURE':
    case 'REVOKED':
      return 'failed'
    case 'STARTED':
      return 'running'
    case 'PENDING':
    default:
      return 'queued'
  }
}

export default function TaskCenter() {
  const [isMounted, setIsMounted] = useState(false)
  const tasks = useTaskStore((state) => state.tasks)
  const updateTask = useTaskStore((state) => state.updateTask)
  const removeTask = useTaskStore((state) => state.removeTask)
  const addToast = useToastStore((state) => state.addToast)

  const activeTasks = useMemo(
    () => tasks.filter((task) => ACTIVE_STATES.has(task.status)),
    [tasks]
  )

  useEffect(() => {
    if (activeTasks.length === 0) return

    let isMounted = true
    const poll = async () => {
      await Promise.all(
        activeTasks.map(async (task) => {
          try {
            const endpoint =
              task.type === 'analysis'
                ? `/repos/${task.repoId}/analyze/${task.id}`
                : `/docs/generate/${task.id}`
            const res = await api.get(endpoint)
            const nextStatus = mapState(res.data?.state)
            if (!isMounted) return
            if (
              task.type === 'docs' &&
              nextStatus === 'completed' &&
              res.data?.result?.status &&
              res.data.result.status !== 'completed'
            ) {
              const resultStatus = res.data.result.status
              const error =
                res.data.result.error ||
                (resultStatus === 'missing_analysis'
                  ? 'Run analysis before generating docs.'
                  : `Docs failed: ${resultStatus}`)
              updateTask(task.id, { status: 'failed' })
              addToast({ message: error, type: 'error' })
              return
            }

            if (task.type === 'analysis' && nextStatus === 'failed' && task.status !== 'failed') {
              const error =
                res.data?.error ||
                res.data?.result?.error ||
                'Analysis failed. Please try again.'
              addToast({ message: error, type: 'error' })
            }

            updateTask(task.id, { status: nextStatus })
          } catch {
            if (!isMounted) return
            updateTask(task.id, { status: 'failed' })
          }
        })
      )
    }

    poll()
    const interval = setInterval(poll, 8000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [activeTasks, updateTask])

  useEffect(() => {
    setIsMounted(true)
  }, [])

  if (!isMounted || tasks.length === 0) return null

  return (
    <div className="fixed bottom-6 right-6 z-40 w-80 space-y-3">
      {tasks.slice(0, 4).map((task) => (
        <div
          key={task.id}
          className="rounded-2xl border border-white/10 bg-slate-950/85 p-4 text-sm text-white/80 shadow-xl"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="text-sm font-semibold text-white">{task.label}</div>
              <div className="text-xs text-white/50">Repo {task.repoId}</div>
            </div>
            <button
              onClick={() => removeTask(task.id)}
              className="text-xs text-white/40 hover:text-white"
            >
              Close
            </button>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs">
            <span
              className={`inline-flex h-2 w-2 rounded-full ${
                task.status === 'completed'
                  ? 'bg-emerald-300'
                  : task.status === 'failed'
                  ? 'bg-red-400'
                  : 'bg-amber-300'
              }`}
            />
            <span className="uppercase tracking-wide text-white/60">{task.status}</span>
            <span className="text-white/30">|</span>
            <span className="text-white/50">
              {task.status === 'queued' && 'Queued'}
              {task.status === 'running' && 'Processing'}
              {task.status === 'completed' && 'Done'}
              {task.status === 'failed' && 'Failed'}
            </span>
          </div>
          {task.status === 'completed' && (
            <div className="mt-3 flex items-center gap-2">
              {task.type === 'docs' ? (
                <a
                  href={`/docs/${task.repoId}`}
                  className="rounded-full border border-emerald-300/40 px-3 py-1 text-xs text-emerald-200"
                >
                  View docs
                </a>
              ) : (
                <a
                  href={`/repos/${task.repoId}`}
                  className="rounded-full border border-white/20 px-3 py-1 text-xs text-white/70"
                >
                  View repo
                </a>
              )}
            </div>
          )}
        </div>
      ))}
      {tasks.length > 4 && (
        <div className="rounded-full border border-white/10 bg-slate-950/80 px-4 py-2 text-xs text-white/60">
          +{tasks.length - 4} more tasks
        </div>
      )}
    </div>
  )
}
