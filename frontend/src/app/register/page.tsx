'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '../../lib/api'
import { useAuthStore } from '../../lib/store/authStore'

type FieldErrors = {
  email?: string
  password?: string
  firstName?: string
}

function getStrength(password: string) {
  let score = 0
  if (password.length >= 8) score += 1
  if (/[A-Z]/.test(password)) score += 1
  if (/[0-9]/.test(password)) score += 1
  if (/[^A-Za-z0-9]/.test(password)) score += 1
  return score
}

function strengthLabel(score: number) {
  if (score <= 1) return 'Weak'
  if (score === 2) return 'Fair'
  if (score === 3) return 'Good'
  return 'Strong'
}

export default function RegisterPage() {
  const router = useRouter()
  const login = useAuthStore((state) => state.login)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [errors, setErrors] = useState<FieldErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const strength = getStrength(password)

  const validate = () => {
    const next: FieldErrors = {}
    if (!email.trim()) {
      next.email = 'Email is required'
    } else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      next.email = 'Enter a valid email'
    }
    if (!password) {
      next.password = 'Password is required'
    } else if (password.length < 6) {
      next.password = 'Password must be at least 6 characters'
    }
    if (!firstName.trim()) {
      next.firstName = 'First name is required'
    } else if (firstName.trim().length < 2) {
      next.firstName = 'First name is too short'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSubmitError(null)
    if (!validate()) return
    setIsLoading(true)

    try {
      await api.post('/auth/register', {
        email,
        password,
        full_name: firstName.trim(),
      })
      await login(email, password, true)
      router.push('/dashboard')
    } catch (err: any) {
      setSubmitError(err?.message || 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6 text-white">
      <div className="w-full max-w-md space-y-4 rounded-2xl border border-white/10 bg-slate-950/80 p-8 shadow-xl">
        <h2 className="text-center text-2xl font-bold font-display">Create your DocuBot account</h2>
        <p className="text-center text-sm text-white/60">
          Start generating README and API docs in minutes.
        </p>
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          <div>
            <label className="block text-sm font-medium text-white/70">Email</label>
            <input
              type="email"
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? 'email-error' : undefined}
              required
            />
            {errors.email && (
              <p id="email-error" className="mt-1 text-sm text-red-300">
                {errors.email}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70">First name</label>
            <input
              type="text"
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
              aria-invalid={!!errors.firstName}
              aria-describedby={errors.firstName ? 'firstname-error' : undefined}
              required
            />
            {errors.firstName && (
              <p id="firstname-error" className="mt-1 text-sm text-red-300">
                {errors.firstName}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70">Password</label>
            <input
              type="password"
              className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              aria-invalid={!!errors.password}
              aria-describedby={errors.password ? 'password-error' : undefined}
              required
            />
            <div className="mt-2 flex items-center gap-2 text-sm text-white/60">
              <div className="h-2 w-full rounded bg-white/10">
                <div
                  className={`h-2 rounded ${
                    strength <= 1
                      ? 'w-1/4 bg-red-400'
                      : strength === 2
                      ? 'w-2/4 bg-yellow-400'
                      : strength === 3
                      ? 'w-3/4 bg-emerald-300'
                      : 'w-full bg-emerald-300'
                  }`}
                />
              </div>
              <span>{strengthLabel(strength)}</span>
            </div>
            {errors.password && (
              <p id="password-error" className="mt-1 text-sm text-red-300">
                {errors.password}
              </p>
            )}
          </div>
          {submitError && (
            <div className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              {submitError}
            </div>
          )}
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/github`}
            className="block w-full rounded-full border border-white/20 px-4 py-2 text-center text-sm text-white/80 transition hover:border-emerald-300/40 hover:text-white"
          >
            Continue with GitHub
          </a>
          <button
            type="submit"
            className="w-full rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
        <div className="text-center text-sm text-white/60">
          Already have an account?{' '}
          <a href="/login" className="text-emerald-200 hover:text-emerald-100">
            Login
          </a>
        </div>
      </div>
    </div>
  )
}
