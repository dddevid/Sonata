import { useEffect, useState, useCallback, useMemo } from 'react'
import { X, Mic2 } from 'lucide-react'
import { usePlayerStore } from '@/stores/playerStore'
import api from '@/api/client'
import { lyricsUrl, coverArtUrl } from '@/api'
import { parseLrc } from '@applemusic-like-lyrics/lyric'
import type { LyricLine } from '@applemusic-like-lyrics/lyric'
import { LyricPlayer } from '@applemusic-like-lyrics/react'

interface LyricsPanelProps {
  isOpen: boolean
  onClose: () => void
}

export default function LyricsPanel({ isOpen, onClose }: LyricsPanelProps) {
  const { currentSong, currentTime, isPlaying } = usePlayerStore()
  const [lyricLines, setLyricLines] = useState<LyricLine[]>([])
  const [plainLines, setPlainLines] = useState<string[]>([])
  const [isSynced, setIsSynced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchLyrics = useCallback(async () => {
    if (!currentSong) return
    setLoading(true)
    setError('')
    try {
      const response = await api.get(lyricsUrl(currentSong.id))
      const lyricsData = response.data?.['subsonic-response']?.lyrics
      const lyricsText: string = lyricsData?.value || ''

      if (lyricsText) {
        const looksLikeLrc = /\[\d{2}:\d{2}[.:]\d{2,3}\]/.test(lyricsText)
        const synced: boolean = lyricsData?.isSynced ?? looksLikeLrc
        if (synced) {
          setLyricLines(parseLrc(lyricsText))
          setPlainLines([])
          setIsSynced(true)
        } else {
          setLyricLines([])
          setPlainLines(lyricsText.split('\n').filter(l => l.trim()))
          setIsSynced(false)
        }
      } else {
        setLyricLines([])
        setPlainLines([])
        setError('No lyrics found for this song')
      }
    } catch {
      setError('Failed to load lyrics')
    } finally {
      setLoading(false)
    }
  }, [currentSong])

  useEffect(() => {
    if (isOpen && currentSong) fetchLyrics()
  }, [isOpen, currentSong, fetchLyrics])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  // Memoized so coverArtUrl/generateSalt only runs on song change, not every 100ms tick
  const bgUrl = useMemo(
    () => (currentSong ? coverArtUrl(`mf-${currentSong.id}`, 300) : undefined),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [currentSong?.id],
  )

  // LyricPlayer requires integer ms
  const currentTimeMs = Math.round(currentTime * 1000)

  const hasContent = lyricLines.length > 0 || plainLines.length > 0

  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-[480px] z-50 flex flex-col overflow-hidden animate-slide-in-right">

      {/* Blurred cover art background */}
      {bgUrl && (
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${bgUrl})`, filter: 'blur(40px) brightness(0.35)', transform: 'scale(1.15)', zIndex: 0 }}
        />
      )}
      {/* Fallback solid bg when no cover */}
      <div className="absolute inset-0 bg-black/60" style={{ zIndex: 1 }} />

      {/* Header */}
      <div className="relative shrink-0 flex items-center justify-between px-6 py-4 border-b border-white/10" style={{ zIndex: 2 }}>
        <div className="flex items-center gap-3">
          <Mic2 size={20} className="text-white/70" />
          <div>
            <h2 className="text-sm font-semibold text-white">
              Lyrics
              {isSynced && (
                <span className="ml-2 text-[10px] font-normal text-white/50 uppercase tracking-wider">synced</span>
              )}
            </h2>
            {currentSong && (
              <p className="text-xs text-white/50 truncate max-w-[280px]">
                {currentSong.title} — {currentSong.artist_name}
              </p>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Body */}
      <div className="relative flex-1 min-h-0" style={{ zIndex: 2 }}>
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white/40" />
          </div>
        ) : !hasContent ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-6">
            <Mic2 size={48} className="text-white/15 mb-4" />
            <p className="text-white/40 text-sm">{error || 'No lyrics available'}</p>
            <p className="text-white/25 text-xs mt-2">Add a .lrc file or embed lyrics in the audio file</p>
          </div>
        ) : isSynced ? (
          <LyricPlayer
            lyricLines={lyricLines}
            currentTime={currentTimeMs}
            playing={isPlaying}
            alignAnchor="center"
            alignPosition={0.35}
            enableSpring
            enableBlur
            enableScale
            wordFadeWidth={0.5}
            onLyricLineClick={(evt) => {
              const line = lyricLines[evt.lineIndex]
              if (line) usePlayerStore.getState().seek(line.startTime / 1000)
            }}
            style={{
              width: '100%',
              height: '100%',
              '--amll-lp-color': 'white',
              '--amll-lp-font-size': '1.2rem',
            } as React.CSSProperties}
          />
        ) : (
          <div className="h-full overflow-y-auto px-8 py-10">
            <div className="space-y-3 pb-24">
              {plainLines.map((line, i) => (
                <p key={i} className="text-white/80 text-base leading-relaxed">
                  {line}
                </p>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
