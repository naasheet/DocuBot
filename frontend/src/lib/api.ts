import axios from 'axios'
import { useToastStore } from './store/toastStore'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    if (!config.headers) {
      config.headers = {}
    }
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    if (status === 401) {
      clearAuthToken()
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
    const message =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      'Request failed'

    const requestUrl = error?.config?.url || ''
    const suppressGithubNotConnected =
      message === 'GitHub account not connected' && requestUrl.includes('/repos')

    if (!suppressGithubNotConnected) {
      try {
        useToastStore.getState().addToast({
          message,
          type: status && status >= 500 ? 'error' : 'info',
        })
      } catch {
        // ignore toast failures
      }
    }

    return Promise.reject({
      status,
      message,
      data: error?.response?.data,
    })
  }
)

export function setAuthToken(token: string | null, persist: boolean = true) {
  if (typeof window === 'undefined') return
  if (token) {
    if (persist) {
      localStorage.setItem('token', token)
      sessionStorage.removeItem('token')
    } else {
      sessionStorage.setItem('token', token)
      localStorage.removeItem('token')
    }
  } else {
    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
  }
}

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('token') || sessionStorage.getItem('token')
}

function clearAuthToken() {
  if (typeof window === 'undefined') return
  localStorage.removeItem('token')
  sessionStorage.removeItem('token')
}
