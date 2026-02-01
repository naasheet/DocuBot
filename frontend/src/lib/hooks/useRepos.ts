import { useState, useEffect } from 'react'
import { api } from '../api'

export function useRepos() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch repositories
    setLoading(false)
  }, [])

  return { repos, loading }
}
