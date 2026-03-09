import { create } from 'zustand'
import { Howl } from 'howler'
import type { Song, QueueItem, RepeatMode } from '@/types'
import { streamUrl } from '@/api'

interface PlayerState {
  queue: QueueItem[]
  currentIndex: number
  isPlaying: boolean
  duration: number
  currentTime: number
  volume: number
  shuffle: boolean
  repeat: RepeatMode
  currentSong: QueueItem | null

  // Actions
  playSong: (song: Song, queue?: Song[]) => void
  playQueue: (songs: Song[], startIndex?: number) => void
  togglePlay: () => void
  pause: () => void
  resume: () => void
  next: () => void
  prev: () => void
  seek: (time: number) => void
  setVolume: (vol: number) => void
  toggleShuffle: () => void
  cycleRepeat: () => void
  addToQueue: (song: Song) => void
  clearQueue: () => void
}

let howl: Howl | null = null
let seekInterval: ReturnType<typeof setInterval> | null = null

function createHowl(url: string, volume: number, onEnd: () => void, onLoad: (duration: number) => void): Howl {
  const h = new Howl({
    src: [url],
    html5: true,
    format: ['mp3', 'flac', 'ogg', 'opus', 'm4a', 'aac', 'wav'],
    volume,
    onend: onEnd,
    onload: () => onLoad(h.duration()),
  })
  return h
}

function generateQueueId(): string {
  return Math.random().toString(36).slice(2)
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  queue: [],
  currentIndex: -1,
  isPlaying: false,
  duration: 0,
  currentTime: 0,
  volume: 0.8,
  shuffle: false,
  repeat: 'none',
  currentSong: null,

  playSong: (song: Song, queue?: Song[]) => {
    const songs = queue || [song]
    const idx = queue ? songs.findIndex((s) => s.id === song.id) : 0
    get().playQueue(songs, idx)
  },

  playQueue: (songs: Song[], startIndex = 0) => {
    const queueItems: QueueItem[] = songs.map((s) => ({ ...s, queueId: generateQueueId() }))
    set({ queue: queueItems, currentIndex: startIndex })
    _loadAndPlay(startIndex, get, set)
  },

  togglePlay: () => {
    if (howl) {
      if (howl.playing()) {
        howl.pause()
        _clearSeekInterval()
        set({ isPlaying: false })
      } else {
        howl.play()
        _startSeekInterval(set, get)
        set({ isPlaying: true })
      }
    }
  },

  pause: () => {
    if (howl?.playing()) {
      howl.pause()
      _clearSeekInterval()
      set({ isPlaying: false })
    }
  },

  resume: () => {
    if (howl && !howl.playing()) {
      howl.play()
      _startSeekInterval(set, get)
      set({ isPlaying: true })
    }
  },

  next: () => {
    const { queue, currentIndex, repeat, shuffle } = get()
    if (!queue.length) return
    let nextIdx: number
    if (shuffle) {
      nextIdx = Math.floor(Math.random() * queue.length)
    } else if (currentIndex < queue.length - 1) {
      nextIdx = currentIndex + 1
    } else if (repeat === 'all') {
      nextIdx = 0
    } else {
      set({ isPlaying: false, currentTime: 0 })
      return
    }
    set({ currentIndex: nextIdx })
    _loadAndPlay(nextIdx, get, set)
  },

  prev: () => {
    const { currentIndex, currentTime } = get()
    // If more than 3s in, restart current song
    if (currentTime > 3) {
      get().seek(0)
      return
    }
    if (currentIndex > 0) {
      const idx = currentIndex - 1
      set({ currentIndex: idx })
      _loadAndPlay(idx, get, set)
    }
  },

  seek: (time: number) => {
    if (howl) {
      howl.seek(time)
      set({ currentTime: time })
    }
  },

  setVolume: (vol: number) => {
    const clamped = Math.max(0, Math.min(1, vol))
    if (howl) howl.volume(clamped)
    set({ volume: clamped })
  },

  toggleShuffle: () => set((s) => ({ shuffle: !s.shuffle })),

  cycleRepeat: () =>
    set((s) => ({
      repeat: s.repeat === 'none' ? 'all' : s.repeat === 'all' ? 'one' : 'none',
    })),

  addToQueue: (song: Song) => {
    const item: QueueItem = { ...song, queueId: generateQueueId() }
    set((s) => ({ queue: [...s.queue, item] }))
  },

  clearQueue: () => {
    howl?.stop()
    howl = null
    _clearSeekInterval()
    set({ queue: [], currentIndex: -1, isPlaying: false, currentSong: null, currentTime: 0, duration: 0 })
  },
}))

function _loadAndPlay(
  idx: number,
  get: () => PlayerState,
  set: (partial: Partial<PlayerState>) => void
) {
  const { queue, volume } = get()
  const song = queue[idx]
  if (!song) return

  howl?.stop()
  howl?.unload()
  _clearSeekInterval()

  const url = streamUrl(song.id)
  howl = createHowl(
    url,
    volume,
    () => {
      // onEnd
      setTimeout(() => {
        const state = get()
        if (state.repeat === 'one') {
          get().seek(0)
          howl?.play()
        } else {
          get().next()
        }
      }, 10)
    },
    (dur) => set({ duration: dur })
  )

  howl.play()
  _startSeekInterval(set, get)
  set({ isPlaying: true, currentSong: song, currentTime: 0, duration: 0 })
}

function _startSeekInterval(set: (partial: Partial<PlayerState>) => void, get: () => PlayerState) {
  _clearSeekInterval()
  seekInterval = setInterval(() => {
    if (howl?.playing()) {
      set({ currentTime: howl.seek() as number })
    }
  }, 500)
}

function _clearSeekInterval() {
  if (seekInterval) {
    clearInterval(seekInterval)
    seekInterval = null
  }
}
