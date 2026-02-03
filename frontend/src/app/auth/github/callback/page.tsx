'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { setAuthToken } from '../../../../lib/api'
import { useAuthStore } from '../../../../lib/store/authStore'

export default function GitHubCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const refreshToken = useAuthStore((state) => state.refreshToken)

  useEffect(() => {
    const token = searchParams.get('token')
    const tokenType = searchParams.get('token_type')

    if (token && tokenType) {
      setAuthToken(token, true)
      refreshToken().finally(() => {
        router.replace('/dashboard')
      })
      return
    }

    const error = searchParams.get('error') || 'GitHub login failed'
    const encoded = encodeURIComponent(error)
    router.replace(`/login?error=${encoded}`)
  }, [router, searchParams])

  return (
    <div className="flex min-h-screen items-center justify-center px-6 text-white">
      <div className="rounded-2xl border border-white/10 bg-slate-950/80 p-6 text-center">
        <div className="text-lg font-semibold">Signing you in...</div>
        <p className="mt-2 text-sm text-white/60">Completing GitHub authentication.</p>
      </div>
    </div>
  )
}
