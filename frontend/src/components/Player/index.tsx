import { useRef, useCallback } from 'react'
import {
  Play, Pause, SkipBack, SkipForward,
  Volume2, VolumeX, Shuffle, Repeat, Repeat1,
  Music2,
} from 'lucide-react'
import { usePlayerStore } from '@/stores/playerStore'
import clsx from 'clsx'
import CoverArt from '@/components/CoverArt'

function formatTime(s: number): string {
  if (isNaN(s) || !isFinite(s)) return '0:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

export default function Player() {
  const {
    currentSong,
    isPlaying,
    currentTime,
    duration,
    volume,
    shuffle,
    repeat,
    togglePlay,
    next,
    prev,
    seek,
    setVolume,
    toggleShuffle,
    cycleRepeat,
  } = usePlayerStore()

  const progressRef = useRef<HTMLDivElement>(null)

  const handleProgressClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!progressRef.current || !duration) return
      const rect = progressRef.current.getBoundingClientRect()
      const ratio = (e.clientX - rect.left) / rect.width
      seek(ratio * duration)
    },
    [seek, duration]
  )

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0
  const coverArtId = currentSong ? `mf-${currentSong.id}` : undefined

  const RepeatIcon = repeat === 'one' ? Repeat1 : Repeat

  return (
    <div className="h-20 bg-surface border-t border-border flex items-center px-4 gap-4 shrink-0">
      {/* Song info */}
      <div className="flex items-center gap-3 w-56 shrink-0">
        <div className="w-12 h-12 rounded-lg overflow-hidden bg-elevated shrink-0">
          {coverArtId ? (
            <CoverArt artId={coverArtId} size={300} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Music2 size={18} className="text-text-muted" />
            </div>
          )}
        </div>
        {currentSong ? (
          <div className="min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">{currentSong.title}</p>
            <p className="text-xs text-text-secondary truncate">{currentSong.artist_name}</p>
          </div>
        ) : (
          <p className="text-sm text-text-muted">Nothing playing</p>
        )}
      </div>

      {/* Center controls */}
      <div className="flex-1 flex flex-col items-center gap-2">
        <div className="flex items-center gap-4">
          {/* Shuffle */}
          <button
            onClick={toggleShuffle}
            className={clsx(
              'p-1.5 rounded-md transition-colors',
              shuffle ? 'text-primary-light' : 'text-text-muted hover:text-text-secondary'
            )}
          >
            <Shuffle size={15} />
          </button>

          {/* Prev */}
          <button
            onClick={prev}
            className="p-1.5 rounded-md text-text-secondary hover:text-text-primary transition-colors"
          >
            <SkipBack size={18} strokeWidth={1.75} />
          </button>

          {/* Play/Pause */}
          <button
            onClick={togglePlay}
            className="w-9 h-9 rounded-full bg-primary hover:bg-primary-hover flex items-center justify-center transition-colors shadow-lg"
          >
            {isPlaying ? (
              <Pause size={16} className="text-white" fill="white" />
            ) : (
              <Play size={16} className="text-white" fill="white" style={{ marginLeft: 1 }} />
            )}
          </button>

          {/* Next */}
          <button
            onClick={next}
            className="p-1.5 rounded-md text-text-secondary hover:text-text-primary transition-colors"
          >
            <SkipForward size={18} strokeWidth={1.75} />
          </button>

          {/* Repeat */}
          <button
            onClick={cycleRepeat}
            className={clsx(
              'p-1.5 rounded-md transition-colors',
              repeat !== 'none' ? 'text-primary-light' : 'text-text-muted hover:text-text-secondary'
            )}
          >
            <RepeatIcon size={15} />
          </button>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-2 w-full max-w-md">
          <span className="text-xs text-text-muted tabular-nums w-8 text-right">
            {formatTime(currentTime)}
          </span>
          <div
            ref={progressRef}
            onClick={handleProgressClick}
            className="flex-1 h-1 bg-border rounded-full cursor-pointer group"
          >
            <div
              className="h-full bg-primary rounded-full relative group-hover:bg-primary-light transition-colors"
              style={{ width: `${progress}%` }}
            >
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity shadow" />
            </div>
          </div>
          <span className="text-xs text-text-muted tabular-nums w-8">
            {formatTime(duration)}
          </span>
        </div>
      </div>

      {/* Volume */}
      <div className="flex items-center gap-2 w-32 justify-end shrink-0">
        <button
          onClick={() => setVolume(volume === 0 ? 0.8 : 0)}
          className="text-text-muted hover:text-text-secondary transition-colors"
        >
          {volume === 0 ? <VolumeX size={16} /> : <Volume2 size={16} />}
        </button>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={volume}
          onChange={(e) => setVolume(Number(e.target.value))}
          className="w-20 accent-primary h-1 cursor-pointer"
        />
      </div>
    </div>
  )
}
