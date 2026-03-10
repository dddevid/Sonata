import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/authStore'
import type { ServerInfo } from '@/types'
import sonataLogo from '@/assets/sonata-logo.svg'

export default function Login() {
  const [serverInfo, setServerInfo] = useState<ServerInfo | null>(null)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const { login, isAuthenticated, setSubsonicCredentials } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true })
  }, [isAuthenticated, navigate])

  useEffect(() => {
    authApi.serverInfo().then(setServerInfo).catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await authApi.login(username, password)
      // Keep plain password only in memory (not in localStorage) for Subsonic token auth
      setSubsonicCredentials(password)
      login(data)
      navigate('/', { replace: true })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <img src={sonataLogo} alt="Sonata" className="h-14 w-auto mb-4" />
          <p className="text-sm text-text-muted mt-1">Your personal music server</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="px-4 py-3 rounded-lg bg-error/10 border border-error/20 text-sm text-error">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label className="block text-xs font-medium text-text-secondary uppercase tracking-wider">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
              className="w-full px-3.5 py-2.5 rounded-lg bg-elevated border border-border text-text-primary placeholder-text-muted text-sm focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition"
              placeholder="your username"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-text-secondary uppercase tracking-wider">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full px-3.5 py-2.5 pr-10 rounded-lg bg-elevated border border-border text-text-primary placeholder-text-muted text-sm focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-2 flex items-center text-text-muted hover:text-text-secondary"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        {/* Register link */}
        {(!serverInfo?.users_exist) && (
          <p className="text-center text-sm text-text-muted mt-6">
            No accounts yet.{' '}
            <Link to="/register" className="text-primary-light hover:underline">
              Create the first account
            </Link>
            <span className="block text-xs mt-1 text-text-muted">(first account becomes admin)</span>
          </p>
        )}
        {serverInfo?.users_exist && serverInfo?.allow_self_register !== false && (
          <p className="text-center text-sm text-text-muted mt-4">
            <Link to="/register" className="text-primary-light hover:underline">
              Create an account
            </Link>
          </p>
        )}
      </div>
    </div>
  )
}
