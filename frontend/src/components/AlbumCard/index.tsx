import { Play } from 'lucide-react'
import type { Album } from '@/types'
import { Link } from 'react-router-dom'
import CoverArt from '@/components/CoverArt'

interface AlbumCardProps {
  album: Album
  onPlay?: () => void
}

export default function AlbumCard({ album, onPlay }: AlbumCardProps) {
  return (
    <div className="group relative">
      <Link to={`/albums/${album.id}`} className="block">
        <div className="relative aspect-square rounded-xl overflow-hidden bg-elevated mb-3">
          <CoverArt
            artId={`al-${album.id}`}
            size={600}
            alt={album.name}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
          />
          {/* Play overlay */}
          {onPlay && (
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <button
                onClick={(e) => {
                  e.preventDefault()
                  onPlay()
                }}
                className="w-12 h-12 rounded-full bg-primary hover:bg-primary-hover flex items-center justify-center shadow-xl transform translate-y-2 group-hover:translate-y-0 transition-transform"
              >
                <Play size={18} fill="white" className="text-white ml-0.5" />
              </button>
            </div>
          )}
        </div>
        <div className="px-0.5">
          <p className="text-sm font-medium text-text-primary truncate">{album.name}</p>
          <p className="text-xs text-text-secondary truncate mt-0.5">{album.artist_name}</p>
          {album.year && (
            <p className="text-xs text-text-muted mt-0.5">{album.year}</p>
          )}
        </div>
      </Link>
    </div>
  )
}
