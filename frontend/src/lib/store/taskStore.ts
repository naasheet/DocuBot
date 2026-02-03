import { create } from 'zustand'

type TaskType = 'analysis' | 'docs'

type TaskStatus = 'queued' | 'running' | 'completed' | 'failed'

export type TaskItem = {
  id: string
  type: TaskType
  repoId: number
  label: string
  status: TaskStatus
  createdAt: number
}

type TaskState = {
  tasks: TaskItem[]
  addTask: (task: TaskItem) => void
  updateTask: (id: string, updates: Partial<TaskItem>) => void
  removeTask: (id: string) => void
}

const storageKey = 'docubot_tasks'

function loadTasks(): TaskItem[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveTasks(tasks: TaskItem[]) {
  if (typeof window === 'undefined') return
  localStorage.setItem(storageKey, JSON.stringify(tasks))
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: loadTasks(),
  addTask: (task) =>
    set((state) => {
      const next = [task, ...state.tasks]
      saveTasks(next)
      return { tasks: next }
    }),
  updateTask: (id, updates) =>
    set((state) => {
      const next = state.tasks.map((task) =>
        task.id === id ? { ...task, ...updates } : task
      )
      saveTasks(next)
      return { tasks: next }
    }),
  removeTask: (id) =>
    set((state) => {
      const next = state.tasks.filter((task) => task.id !== id)
      saveTasks(next)
      return { tasks: next }
    }),
}))
