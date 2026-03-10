import { NavLink, useNavigate } from 'react-router-dom'
import {
  Home,
  Mic2,
  Disc3,
  ListMusic,
  Search,
  LogOut,
  Shield,
} from 'lucide-react'
import sonataLogo from '@/assets/sonata-logo.svg'
import { useAuthStore } from '@/stores/authStore'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: Home, label: 'Home', exact: true },
  { to: '/artists', icon: Mic2, label: 'Artists' },
  { to: '/albums', icon: Disc3, label: 'Albums' },
  { to: '/playlists', icon: ListMusic, label: 'Playlists' },
  { to: '/search', icon: Search, label: 'Search' },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="w-56 shrink-0 flex flex-col bg-surface border-r border-border">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <img src={sonataLogo} alt="Sonata" className="h-8 w-auto" />
          <span className="text-base font-semibold text-text-primary tracking-tight">Sonata</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto scrollbar-none">
        <div className="space-y-0.5">
          {navItems.map(({ to, icon: Icon, label, exact }) => (
            <NavLink
              key={to}
              to={to}
              end={exact}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                  isActive
                    ? 'bg-primary/15 text-primary-light'
                    : 'text-text-secondary hover:text-text-primary hover:bg-elevated'
                )
              }
            >
              <Icon size={16} strokeWidth={1.75} />
              {label}
            </NavLink>
          ))}
        </div>

        {user?.isAdmin && (
          <div className="mt-6 pt-4 border-t border-border">
            <p className="px-3 mb-2 text-xs font-semibold text-text-muted uppercase tracking-wider">
              Admin
            </p>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary/15 text-primary-light'
                    : 'text-text-secondary hover:text-text-primary hover:bg-elevated'
                )
              }
            >
              <Shield size={16} strokeWidth={1.75} />
              Admin Panel
            </NavLink>
          </div>
        )}
      </nav>

      {/* User section */}
      <div className="px-3 py-3 border-t border-border">
        <div className="flex items-center gap-2.5 px-2 py-2">
          <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
            <span className="text-xs font-semibold text-primary-light uppercase">
              {user?.username?.[0] ?? '?'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">{user?.username}</p>
            <p className="text-xs text-text-muted capitalize">{user?.role}</p>
          </div>
          <button
            onClick={handleLogout}
            title="Log out"
            className="p-1.5 rounded-md text-text-muted hover:text-error hover:bg-error/10 transition-colors"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  )
}
