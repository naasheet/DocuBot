'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '../lib/store/authStore'

export default function AuthHomeRedirect() {
  const router = useRouter()
  const token = useAuthStore((state) => state.token)
  const hydrate = useAuthStore((state) => state.hydrate)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  useEffect(() => {
    if (token) {
      router.replace('/dashboard')
    }
  }, [token, router])

  return null
}
