import { create } from 'zustand'
import { api, setAuthToken } from '../api'

type AuthUser = {
  id: number
  email: string
  full_name?: string | null
}

interface AuthState {
  user: AuthUser | null
  token: string | null
  isLoading: boolean
  error: string | null
  setUser: (user: AuthUser | null) => void
  login: (email: string, password: string, remember?: boolean) => Promise<void>
  loginWithCode: (email: string, code: string, remember?: boolean) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  updateName: (firstName: string) => Promise<void>
  hydrate: () => void
}

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token') || sessionStorage.getItem('token')
}

function setStoredToken(token: string | null) {
  if (typeof window === 'undefined') return
  if (token) {
    localStorage.setItem('token', token)
    sessionStorage.removeItem('token')
  } else {
    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isLoading: false,
  error: null,
  setUser: (user) => set({ user }),
  hydrate: () => {
    const token = getStoredToken()
    if (token) {
      set({ token })
      setAuthToken(token, true)
    }
  },
  login: async (email, password, remember = true) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/auth/login', { email, password })
      const token = response.data?.access_token as string
      if (!token) {
        throw new Error('No access token returned')
      }
      if (remember) {
        setStoredToken(token)
      } else {
        setStoredToken(null)
      }
      setAuthToken(token, remember)
      set({ token })

      const me = await api.get('/auth/me')
      set({ user: me.data, isLoading: false })
    } catch (err: any) {
      set({ error: err?.message || 'Login failed', isLoading: false })
      throw err
    }
  },
  loginWithCode: async (email, code, remember = true) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/auth/login/code', { email, code })
      const token = response.data?.access_token as string
      if (!token) {
        throw new Error('No access token returned')
      }
      if (remember) {
        setStoredToken(token)
      } else {
        setStoredToken(null)
      }
      setAuthToken(token, remember)
      set({ token })

      const me = await api.get('/auth/me')
      set({ user: me.data, isLoading: false })
    } catch (err: any) {
      set({ error: err?.message || 'Login failed', isLoading: false })
      throw err
    }
  },
  logout: () => {
    setStoredToken(null)
    setAuthToken(null)
    set({ user: null, token: null })
  },
  refreshToken: async () => {
    const token = get().token || getStoredToken()
    if (!token) {
      get().logout()
      return
    }
    setAuthToken(token)
    try {
      const me = await api.get('/auth/me')
      set({ user: me.data })
    } catch {
      get().logout()
    }
  },
  updateName: async (firstName: string) => {
    const name = firstName.trim()
    if (!name) {
      throw new Error('First name is required')
    }
    const response = await api.patch('/auth/me', { full_name: name })
    set({ user: response.data })
  },
}))
