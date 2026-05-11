import { NavLink } from 'react-router-dom'
import { Home, Mic2, Disc3, ListMusic, Search } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: Home, label: 'Home', exact: true },
  { to: '/artists', icon: Mic2, label: 'Artists' },
  { to: '/albums', icon: Disc3, label: 'Albums' },
  { to: '/playlists', icon: ListMusic, label: 'Playlists' },
  { to: '/search', icon: Search, label: 'Search' },
]

export default function BottomNav() {
  return (
    <nav className="md:hidden flex items-center justify-around bg-surface border-t border-border shrink-0 pb-safe">
      {navItems.map(({ to, icon: Icon, label, exact }) => (
        <NavLink
          key={to}
          to={to}
          end={exact}
          className={({ isActive }) =>
            clsx(
              'flex flex-col items-center gap-1 py-2 px-3 text-[10px] font-medium transition-colors',
              isActive ? 'text-primary-light' : 'text-text-muted'
            )
          }
        >
          <Icon size={20} strokeWidth={1.75} />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
