import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Play, Shuffle, Clock, ArrowLeft, Trash2 } from 'lucide-react'
import { playlistApi } from '@/api'
import { usePlayerStore } from '@/stores/playerStore'
import type { Song } from '@/types'
import CoverArt from '@/components/CoverArt'

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function PlaylistDetail() {
  const { id } = useParams<{ id: string }>()
  const { playQueue, currentSong } = usePlayerStore()
  const qc = useQueryClient()

  const { data: playlist, isLoading, error } = useQuery({
    queryKey: ['playlist', id],
    queryFn: () => playlistApi.get(Number(id)),
    enabled: !!id,
  })

  const removeSong = useMutation({
    mutationFn: (songId: number) => {
      const songs = playlist!.songs!.filter((s) => s.id !== songId)
      return playlistApi.update(Number(id), { song_ids: songs.map((s) => s.id) } as any)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['playlist', id] }),
  })

  const handlePlayAll = () => {
    if (playlist?.songs?.length) playQueue(playlist.songs)
  }

  const handleShuffle = () => {
    if (playlist?.songs?.length) {
      const shuffled = [...playlist.songs].sort(() => Math.random() - 0.5)
      playQueue(shuffled)
    }
  }

  const totalDuration = playlist?.songs?.reduce((acc, s) => acc + s.duration, 0) ?? 0

  if (isLoading) {
    return (
      <div className="p-6 animate-fade-in space-y-4">
        <div className="h-6 w-32 bg-elevated rounded animate-pulse" />
        <div className="flex items-end gap-8">
          <div className="w-48 h-48 rounded-xl bg-elevated animate-pulse flex-shrink-0" />
          <div className="space-y-3 flex-1">
            <div className="h-8 w-64 bg-elevated rounded animate-pulse" />
            <div className="h-4 w-40 bg-elevated rounded animate-pulse" />
          </div>
        </div>
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="h-10 bg-elevated rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (error || !playlist) {
    return (
      <div className="p-6 flex flex-col items-center justify-center py-24">
        <p className="text-text-secondary">Playlist not found</p>
        <Link to="/playlists" className="mt-4 text-sm text-primary-light hover:underline">← Back to Playlists</Link>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <div className="relative px-6 py-10 flex items-end gap-8">
        <div className="w-48 h-48 rounded-xl overflow-hidden shadow-2xl flex-shrink-0 bg-surface">
          {playlist.id ? (
            <CoverArt artId={`pl-${playlist.id}`} size={600} alt={playlist.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-5xl">🎵</div>
          )}
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">Playlist</p>
          <h1 className="text-4xl font-bold text-text-primary leading-tight">{playlist.name}</h1>
          {playlist.comment && <p className="text-sm text-text-secondary mt-1">{playlist.comment}</p>}
          <p className="text-sm text-text-muted mt-2">
            {playlist.song_count} song{playlist.song_count !== 1 ? 's' : ''} · {formatDuration(totalDuration)}
          </p>
          <div className="flex items-center gap-3 mt-6">
            <button
              onClick={handlePlayAll}
              disabled={!playlist.songs?.length}
              className="flex items-center gap-2 bg-primary-light hover:bg-primary disabled:opacity-50 text-white text-sm font-semibold px-6 py-2.5 rounded-full transition-colors"
            >
              <Play size={14} fill="white" /> Play
            </button>
            <button
              onClick={handleShuffle}
              disabled={!playlist.songs?.length}
              className="flex items-center gap-2 bg-elevated hover:bg-border disabled:opacity-50 text-text-primary text-sm font-semibold px-5 py-2.5 rounded-full transition-colors"
            >
              <Shuffle size={14} /> Shuffle
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 pb-6">
        <Link to="/playlists" className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors mb-6">
          <ArrowLeft size={12} /> All Playlists
        </Link>

        {playlist.songs && playlist.songs.length > 0 ? (
          <div>
            <div className="grid grid-cols-[2rem_1fr_auto_auto] gap-4 items-center px-4 py-1 mb-1 border-b border-border">
              <span className="text-xs text-text-muted text-center">#</span>
              <span className="text-xs text-text-muted">Title</span>
              <span className="text-xs text-text-muted">Artist / Album</span>
              <Clock size={12} className="text-text-muted" />
            </div>
            <div className="space-y-0.5 mt-2">
              {playlist.songs.map((song, i) => (
                <div
                  key={song.id}
                  className="group grid grid-cols-[2rem_1fr_auto_auto] gap-4 items-center px-4 py-2 rounded-lg cursor-pointer hover:bg-elevated transition-colors"
                  onClick={() => playQueue(playlist.songs!, i)}
                >
                  <div className="text-center">
                    {currentSong?.id === song.id ? (
                      <span className="text-primary-light text-xs">♪</span>
                    ) : (
                      <>
                        <span className="text-text-muted text-xs group-hover:hidden">{i + 1}</span>
                        <Play size={12} className="text-text-primary hidden group-hover:block mx-auto" />
                      </>
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className={`text-sm font-medium truncate ${currentSong?.id === song.id ? 'text-primary-light' : 'text-text-primary'}`}>
                      {song.title}
                    </p>
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs text-text-muted truncate max-w-[200px]">
                      {song.artist} {song.album && `· ${song.album}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-text-muted tabular-nums">{formatDuration(song.duration)}</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); removeSong.mutate(song.id) }}
                      className="p-1 opacity-0 group-hover:opacity-100 hover:text-red-400 text-text-muted transition-all"
                      title="Remove from playlist"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16">
            <span className="text-3xl mb-3">🎵</span>
            <p className="text-text-secondary text-sm">This playlist is empty</p>
          </div>
        )}
      </div>
    </div>
  )
}
