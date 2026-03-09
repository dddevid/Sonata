import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/Sidebar'
import Player from '@/components/Player'
import NowPlayingAdmin from '@/components/NowPlayingAdmin'
import { usePlayerStore } from '@/stores/playerStore'

export default function Layout() {
  const togglePlay = usePlayerStore((s) => s.togglePlay)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore space if typing in an input or textarea
      const target = e.target as HTMLElement
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable

      if (e.code === 'Space' && !isInput) {
        e.preventDefault() // prevent page scroll OR focused button click
        togglePlay()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [togglePlay])

  return (
    <div className="flex h-screen overflow-hidden bg-base">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
        {/* Player bar */}
        <Player />
      </main>

      {/* Admin Overlay */}
      <NowPlayingAdmin />
    </div>
  )
}
