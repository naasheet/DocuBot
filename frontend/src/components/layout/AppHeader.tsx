'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { useAuthStore } from '../../lib/store/authStore'
import ConnectGitHubLink from '../ConnectGitHubLink'

const navItems = [
  { href: '/', label: 'Home' },
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/repos', label: 'Repos' },
  { href: '/docs', label: 'Docs' },
  { href: '/chat', label: 'Chat' },
]

export default function AppHeader() {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const hydrate = useAuthStore((state) => state.hydrate)
  const refreshToken = useAuthStore((state) => state.refreshToken)
  const logout = useAuthStore((state) => state.logout)

  useEffect(() => {
    hydrate()
  }, [hydrate])

  useEffect(() => {
    if (token && !user) {
      refreshToken()
    }
  }, [token, user, refreshToken])

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/70 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-lg font-semibold tracking-tight text-white">DocuBot</span>
          <span className="rounded-full border border-white/20 px-2 py-0.5 text-[11px] uppercase tracking-widest text-white/70">
            MVP
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-sm text-white/70 md:flex">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="transition hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-3 text-sm text-white/70">
              <span>{user.full_name || user.email}</span>
              <ConnectGitHubLink className="rounded-full border border-white/20 px-3 py-1.5 text-xs text-white/70 hover:text-white" />
              <button
                onClick={logout}
                className="rounded-full border border-white/20 px-3 py-1.5 text-xs text-white/70 hover:text-white"
              >
                Logout
              </button>
            </div>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm text-white/70 transition hover:text-white"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 transition hover:-translate-y-0.5 hover:bg-white/90"
              >
                Get started
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
