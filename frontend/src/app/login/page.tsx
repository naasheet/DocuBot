'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuthStore } from '../../lib/store/authStore'
import { api } from '../../lib/api'

type FieldErrors = {
  email?: string
  password?: string
}

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const login = useAuthStore((state) => state.login)
  const loginWithCode = useAuthStore((state) => state.loginWithCode)
  const isLoading = useAuthStore((state) => state.isLoading)
  const apiError = useAuthStore((state) => state.error)
  const oauthError = searchParams.get('error')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(true)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [forgotOpen, setForgotOpen] = useState(false)
  const [forgotMethod, setForgotMethod] = useState<'reset' | 'login'>('reset')
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotCode, setForgotCode] = useState('')
  const [forgotNewPassword, setForgotNewPassword] = useState('')
  const [forgotStep, setForgotStep] = useState<'request' | 'verify' | 'done'>('request')
  const [forgotMessage, setForgotMessage] = useState<string | null>(null)
  const [forgotError, setForgotError] = useState<string | null>(null)
  const [forgotLoading, setForgotLoading] = useState(false)

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
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSubmitError(null)
    if (!validate()) return

    try {
      await login(email, password, remember)
      router.push('/dashboard')
    } catch (err: any) {
      setSubmitError(err?.message || 'Login failed')
    }
  }

  const openForgot = () => {
    setForgotOpen(true)
    setForgotMethod('reset')
    setForgotEmail(email)
    setForgotCode('')
    setForgotNewPassword('')
    setForgotStep('request')
    setForgotMessage(null)
    setForgotError(null)
  }

  const handleForgotRequest = async (event: React.FormEvent) => {
    event.preventDefault()
    setForgotError(null)
    setForgotMessage(null)
    if (!forgotEmail.trim()) {
      setForgotError('Email is required')
      return
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(forgotEmail)) {
      setForgotError('Enter a valid email')
      return
    }
    setForgotLoading(true)
    try {
      const response = await api.post('/auth/forgot', {
        email: forgotEmail,
        method: forgotMethod,
      })
      setForgotMessage(response.data?.message || 'Check your email for a code.')
      setForgotStep('verify')
    } catch (err: any) {
      setForgotError(err?.message || 'Unable to send code')
    } finally {
      setForgotLoading(false)
    }
  }

  const handleForgotVerify = async (event: React.FormEvent) => {
    event.preventDefault()
    setForgotError(null)
    setForgotMessage(null)
    if (!forgotCode.trim()) {
      setForgotError('Code is required')
      return
    }
    setForgotLoading(true)
    try {
      if (forgotMethod === 'reset') {
        if (!forgotNewPassword || forgotNewPassword.length < 8) {
          setForgotError('Password must be at least 8 characters')
          setForgotLoading(false)
          return
        }
        await api.post('/auth/reset', {
          email: forgotEmail,
          code: forgotCode,
          new_password: forgotNewPassword,
        })
        setForgotMessage('Password reset successfully. You can log in now.')
        setForgotStep('done')
      } else {
        await loginWithCode(forgotEmail, forgotCode, remember)
        router.push('/dashboard')
      }
    } catch (err: any) {
      setForgotError(err?.message || 'Unable to verify code')
    } finally {
      setForgotLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6 text-white">
      <div className="w-full max-w-md space-y-4 rounded-2xl border border-white/10 bg-slate-950/80 p-8 shadow-xl">
        <h2 className="text-center text-2xl font-bold font-display">Login to DocuBot</h2>
        <p className="text-center text-sm text-white/60">
          Welcome back. Sign in to continue.
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
            {errors.password && (
              <p id="password-error" className="mt-1 text-sm text-red-300">
                {errors.password}
              </p>
            )}
          </div>
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-white/70">
              <input
                type="checkbox"
                checked={remember}
                onChange={(event) => setRemember(event.target.checked)}
                className="h-4 w-4 rounded border-white/20 bg-slate-950/40"
              />
              Remember me
            </label>
            <button
              type="button"
              className="text-sm text-emerald-200 hover:text-emerald-100"
              onClick={openForgot}
            >
              Forgot password?
            </button>
          </div>
          <div className="text-right">
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/github`}
              className="text-sm text-emerald-200 hover:text-emerald-100"
            >
              Login with GitHub
            </a>
          </div>
          {(submitError || apiError || oauthError) && (
            <div className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              {submitError || apiError || oauthError}
            </div>
          )}
          <button
            type="submit"
            className="w-full rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Login'}
          </button>
        </form>
        <div className="text-center text-sm text-white/60">
          Don&apos;t have an account?{' '}
          <a href="/register" className="text-emerald-200 hover:text-emerald-100">
            Create one
          </a>
        </div>
      </div>
      {forgotOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950 p-6 text-white shadow-2xl">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold">Forgot password</h3>
                <p className="mt-1 text-sm text-white/60">
                  Choose how you want to get a code.
                </p>
              </div>
              <button
                type="button"
                className="text-white/60 hover:text-white"
                onClick={() => setForgotOpen(false)}
              >
                ✕
              </button>
            </div>
            {forgotStep === 'request' && (
              <form className="mt-4 space-y-4" onSubmit={handleForgotRequest}>
                <div className="space-y-2 rounded-xl border border-white/10 bg-slate-950/60 p-3">
                  <label className="flex items-center gap-2 text-sm text-white/70">
                    <input
                      type="radio"
                      name="forgot-method"
                      value="reset"
                      checked={forgotMethod === 'reset'}
                      onChange={() => setForgotMethod('reset')}
                      className="h-4 w-4"
                    />
                    Reset password with a code
                  </label>
                  <label className="flex items-center gap-2 text-sm text-white/70">
                    <input
                      type="radio"
                      name="forgot-method"
                      value="login"
                      checked={forgotMethod === 'login'}
                      onChange={() => setForgotMethod('login')}
                      className="h-4 w-4"
                    />
                    Login with a one-time code
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/70">Email</label>
                  <input
                    type="email"
                    className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
                    value={forgotEmail}
                    onChange={(event) => setForgotEmail(event.target.value)}
                  />
                </div>
                {forgotError && (
                  <div className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                    {forgotError}
                  </div>
                )}
                {forgotMessage && (
                  <div className="rounded border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-100">
                    {forgotMessage}
                  </div>
                )}
                <button
                  type="submit"
                  className="w-full rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
                  disabled={forgotLoading}
                >
                  {forgotLoading ? 'Sending...' : 'Send code'}
                </button>
              </form>
            )}
            {forgotStep === 'verify' && (
              <form className="mt-4 space-y-4" onSubmit={handleForgotVerify}>
                <div>
                  <label className="block text-sm font-medium text-white/70">Email</label>
                  <input
                    type="email"
                    className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
                    value={forgotEmail}
                    onChange={(event) => setForgotEmail(event.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/70">Code</label>
                  <input
                    type="text"
                    className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
                    value={forgotCode}
                    onChange={(event) => setForgotCode(event.target.value)}
                  />
                </div>
                {forgotMethod === 'reset' && (
                  <div>
                    <label className="block text-sm font-medium text-white/70">New password</label>
                    <input
                      type="password"
                      className="w-full rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white placeholder:text-white/40 focus:border-emerald-300/40 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
                      value={forgotNewPassword}
                      onChange={(event) => setForgotNewPassword(event.target.value)}
                    />
                  </div>
                )}
                {forgotError && (
                  <div className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                    {forgotError}
                  </div>
                )}
                {forgotMessage && (
                  <div className="rounded border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-100">
                    {forgotMessage}
                  </div>
                )}
                <button
                  type="submit"
                  className="w-full rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-50"
                  disabled={forgotLoading}
                >
                  {forgotLoading ? 'Verifying...' : forgotMethod === 'reset' ? 'Reset password' : 'Login with code'}
                </button>
              </form>
            )}
            {forgotStep === 'done' && (
              <div className="mt-4 space-y-4">
                <div className="rounded border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-100">
                  {forgotMessage || 'Password reset successfully.'}
                </div>
                <button
                  type="button"
                  className="w-full rounded-full bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-900"
                  onClick={() => setForgotOpen(false)}
                >
                  Back to login
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
