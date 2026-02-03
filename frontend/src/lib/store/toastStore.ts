import { create } from 'zustand'

export type Toast = {
  id: string
  message: string
  type?: 'success' | 'error' | 'info'
  duration?: number
}

type ToastState = {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  addToast: (toast) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    const duration = toast.duration ?? 4000
    set({ toasts: [...get().toasts, { ...toast, id }] })
    if (duration > 0) {
      setTimeout(() => {
        get().removeToast(id)
      }, duration)
    }
  },
  removeToast: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
}))
