'use client'

import { useState, useEffect } from 'react'
import { api } from '../api'

export function useRepos() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    const fetchRepos = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await api.get('/repos')
        if (isMounted) {
          setRepos(response.data || [])
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err?.message || 'Failed to load repositories')
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchRepos()
    return () => {
      isMounted = false
    }
  }, [])

  return { repos, loading, error }
}
