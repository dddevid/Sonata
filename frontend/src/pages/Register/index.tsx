import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Music2, Eye, EyeOff } from 'lucide-react'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/authStore'
import type { ServerInfo } from '@/types'

export default function Register() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [serverInfo, setServerInfo] = useState<ServerInfo | null>(null)
  const { login, setSubsonicCredentials } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    authApi
      .serverInfo()
      .then((info) => {
        setServerInfo(info)
        if (info.users_exist && info.allow_self_register === false) {
          navigate('/login', { replace: true })
        }
      })
      .catch(() => {})
  }, [navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password.length < 4) {
      setError('Password must be at least 4 characters')
      return
    }
    setLoading(true)
    try {
      const data = await authApi.register(username, email, password)
      // Keep plain password only in memory (not in localStorage) for Subsonic token auth
      setSubsonicCredentials(password)
      login(data)
      navigate('/', { replace: true })
    } catch (err: any) {
      const errors = err.response?.data
      if (errors?.username) setError(`Username: ${errors.username[0]}`)
      else if (errors?.password) setError(`Password: ${errors.password[0]}`)
      else setError(errors?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-base flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-primary flex items-center justify-center mb-4 shadow-lg shadow-primary/20">
            <Music2 size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-text-primary">
            {serverInfo?.users_exist ? 'Create account' : 'Create the first account'}
          </h1>
          <p className="text-sm text-text-muted mt-1">
            {serverInfo?.users_exist
              ? 'Create a new user for this server'
              : 'The first account becomes admin'}
          </p>
        </div>

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
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
              className="w-full px-3.5 py-2.5 rounded-lg bg-elevated border border-border text-text-primary placeholder-text-muted text-sm focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition"
              placeholder="cooluser"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-text-secondary uppercase tracking-wider">
              Email (optional)
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              className="w-full px-3.5 py-2.5 rounded-lg bg-elevated border border-border text-text-primary placeholder-text-muted text-sm focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition"
              placeholder="you@example.com"
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-medium text-text-secondary uppercase tracking-wider">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
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
            className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary-hover text-white text-sm font-semibold transition-colors disabled:opacity-50 mt-2"
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="text-center text-sm text-text-muted mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-light hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
