import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/api'
import { useAuthStore } from '@/stores/authStore'
import { Music2, ChevronDown, ChevronUp } from 'lucide-react'
import CoverArt from '@/components/CoverArt'

export default function NowPlayingAdmin() {
  const { user } = useAuthStore()
  const [minimised, setMinimised] = useState(false)

  const { data } = useQuery({
    queryKey: ['admin', 'nowPlaying'],
    queryFn: adminApi.getNowPlaying,
    refetchInterval: 10000,
    enabled: !!user?.isAdmin,
  })

  if (!user?.isAdmin) return null

  const entries = data?.['subsonic-response']?.nowPlaying?.entry || []
  const activeStreams: any[] = Array.isArray(entries) ? entries : [entries].filter(Boolean)

  if (activeStreams.length === 0) return null

  return (
    <div className="absolute top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">

      {/* Header row: label + toggle */}
      <div className="flex items-center justify-end gap-2">
        <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
          Admin: Now Playing
          {minimised && (
            <span className="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full bg-primary text-white text-[9px] font-bold">
              {activeStreams.length}
            </span>
          )}
        </span>
        <button
          onClick={() => setMinimised(m => !m)}
          className="p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-elevated transition-colors"
          title={minimised ? 'Expand' : 'Minimise'}
        >
          {minimised ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
        </button>
      </div>

      {/* Stream cards */}
      {!minimised && activeStreams.map((stream: any) => (
        <div
          key={`${stream.username}-${stream.id}-${stream.playerId}`}
          className="bg-elevated/90 backdrop-blur-md border border-border shadow-lg rounded-xl p-3 flex items-center gap-3 animate-fade-in"
        >
          <div className="w-10 h-10 rounded-md overflow-hidden bg-surface flex-shrink-0">
            {stream.coverArt ? (
              <CoverArt artId={stream.coverArt} size={120} alt="" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Music2 size={16} className="text-text-muted" />
              </div>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-text-primary flex items-center gap-1">
              <span className="truncate text-primary-light font-semibold">{stream.username}</span>
              <span className="text-[10px] text-text-muted bg-surface px-1.5 py-0.5 rounded-sm shrink-0">{stream.playerId}</span>
            </p>
            <p className="text-sm text-text-primary truncate font-medium">{stream.title}</p>
            <p className="text-xs text-text-secondary truncate">{stream.artist}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
