import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Music, Play } from 'lucide-react'
import { playlistApi } from '@/api'
import { usePlayerStore } from '@/stores/playerStore'
import type { Playlist } from '@/types'
import CoverArt from '@/components/CoverArt'

function PlaylistRow({ playlist, onDelete }: { playlist: Playlist; onDelete: (id: number) => void }) {
  const { playQueue } = usePlayerStore()

  const handlePlay = async (e: React.MouseEvent) => {
    e.preventDefault()
    try {
      const full = await playlistApi.get(playlist.id)
      if (full.songs?.length) playQueue(full.songs)
    } catch {}
  }

  return (
    <Link
      to={`/playlists/${playlist.id}`}
      className="group flex items-center gap-4 px-4 py-3 rounded-xl hover:bg-elevated transition-colors"
    >
      {/* Cover */}
      <div className="w-12 h-12 rounded-lg bg-surface flex items-center justify-center flex-shrink-0 overflow-hidden">
        {playlist.id ? (
          <CoverArt artId={`pl-${playlist.id}`} size={600} alt={playlist.name} className="w-full h-full object-cover" />
        ) : (
          <Music size={20} className="text-text-muted" />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary truncate">{playlist.name}</p>
        <p className="text-xs text-text-muted">
          {playlist.song_count} song{playlist.song_count !== 1 ? 's' : ''}
          {playlist.comment && ` · ${playlist.comment}`}
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={handlePlay}
          className="p-1.5 rounded-full hover:bg-border text-text-secondary hover:text-text-primary transition-colors"
          title="Play"
        >
          <Play size={14} />
        </button>
        <button
          onClick={(e) => { e.preventDefault(); onDelete(playlist.id) }}
          className="p-1.5 rounded-full hover:bg-border text-text-secondary hover:text-red-400 transition-colors"
          title="Delete"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </Link>
  )
}

function CreateModal({ onClose, onCreate }: { onClose: () => void; onCreate: (name: string, comment: string) => void }) {
  const [name, setName] = useState('')
  const [comment, setComment] = useState('')

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-surface border border-border rounded-2xl p-6 w-full max-w-sm shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-semibold text-text-primary mb-5">New Playlist</h2>
        <div className="space-y-3">
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
            className="w-full bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light"
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="w-full bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light"
          />
        </div>
        <div className="flex justify-end gap-3 mt-5">
          <button onClick={onClose} className="text-sm text-text-secondary hover:text-text-primary px-4 py-2 rounded-lg hover:bg-elevated transition-colors">
            Cancel
          </button>
          <button
            onClick={() => name.trim() && onCreate(name.trim(), comment.trim())}
            disabled={!name.trim()}
            className="text-sm font-medium bg-primary-light hover:bg-primary disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Create
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Playlists() {
  const [showCreate, setShowCreate] = useState(false)
  const qc = useQueryClient()

  const { data: playlists = [], isLoading } = useQuery({
    queryKey: ['playlists'],
    queryFn: playlistApi.list,
  })

  const createMutation = useMutation({
    mutationFn: ({ name, comment }: { name: string; comment: string }) =>
      playlistApi.create(name, comment),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['playlists'] }); setShowCreate(false) },
  })

  const deleteMutation = useMutation({
    mutationFn: playlistApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['playlists'] }),
  })

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Playlists</h1>
          <p className="text-sm text-text-secondary mt-1">
            {playlists.length} playlist{playlists.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-primary-light hover:bg-primary text-white text-sm font-medium px-4 py-2 rounded-full transition-colors"
        >
          <Plus size={14} /> New Playlist
        </button>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-16 bg-elevated rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && playlists.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24">
          <span className="text-4xl mb-3">🎵</span>
          <p className="text-text-secondary text-sm mb-3">No playlists yet</p>
          <button
            onClick={() => setShowCreate(true)}
            className="text-sm text-primary-light hover:underline"
          >
            Create your first playlist
          </button>
        </div>
      )}

      {!isLoading && playlists.length > 0 && (
        <div className="space-y-1">
          {playlists.map((playlist) => (
            <PlaylistRow
              key={playlist.id}
              playlist={playlist}
              onDelete={(id) => deleteMutation.mutate(id)}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <CreateModal
          onClose={() => setShowCreate(false)}
          onCreate={(name, comment) => createMutation.mutate({ name, comment })}
        />
      )}
    </div>
  )
}
