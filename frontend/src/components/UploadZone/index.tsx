import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { uploadApi, type UploadFileResult } from '@/api'

// Audio extensions the server accepts
const AUDIO_EXTS = new Set([
  'mp3', 'flac', 'ogg', 'oga', 'opus', 'm4a', 'mp4', 'aac', 'wav', 'aiff', 'aif', 'wma',
])

function isAudio(file: File) {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  return AUDIO_EXTS.has(ext)
}

type FileState = {
  file: File
  status: 'pending' | 'uploading' | 'ok' | 'skipped' | 'error'
  reason?: string
}

// ─────────────────────────────────────────────────────────────────────────────

export default function UploadZone() {
  const user = useAuthStore((s) => s.user)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [overallPct, setOverallPct] = useState(0)
  const [files, setFiles] = useState<FileState[]>([])
  const [uploading, setUploading] = useState(false)
  const [done, setDone] = useState(false)
  const dragCounter = useRef(0)

  // Only admins can upload
  if (!user?.isAdmin) return null

  // ── Global drag listeners ───────────────────────────────────────────────────

  const handleDragEnter = useCallback((e: DragEvent) => {
    e.preventDefault()
    dragCounter.current++
    if (dragCounter.current === 1) setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault()
    dragCounter.current--
    if (dragCounter.current === 0) setIsDragOver(false)
  }, [])

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault()
  }, [])

  // Recursively collect files from a DataTransferItem (supports folders)
  async function collectFiles(item: DataTransferItem): Promise<File[]> {
    const entry = item.webkitGetAsEntry?.()
    if (!entry) {
      const f = item.getAsFile()
      return f ? [f] : []
    }
    return readEntry(entry)
  }

  async function readEntry(entry: FileSystemEntry): Promise<File[]> {
    if (entry.isFile) {
      return new Promise((resolve) => {
        ;(entry as FileSystemFileEntry).file(
          (f) => resolve([f]),
          () => resolve([]),
        )
      })
    }
    if (entry.isDirectory) {
      const reader = (entry as FileSystemDirectoryEntry).createReader()
      const all: File[] = []
      await new Promise<void>((resolve) => {
        const read = () => {
          reader.readEntries(async (entries) => {
            if (entries.length === 0) return resolve()
            for (const e of entries) all.push(...(await readEntry(e)))
            read()
          })
        }
        read()
      })
      return all
    }
    return []
  }

  const handleDrop = useCallback(async (e: DragEvent) => {
    e.preventDefault()
    dragCounter.current = 0
    setIsDragOver(false)

    const items = Array.from(e.dataTransfer?.items ?? [])
    const allFiles: File[] = []
    for (const item of items) {
      allFiles.push(...(await collectFiles(item)))
    }

    const audio = allFiles.filter(isAudio)
    if (audio.length === 0) return

    setFiles(audio.map((f) => ({ file: f, status: 'pending' })))
    setOverallPct(0)
    setDone(false)
    setIsOpen(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    window.addEventListener('dragenter', handleDragEnter)
    window.addEventListener('dragleave', handleDragLeave)
    window.addEventListener('dragover', handleDragOver)
    window.addEventListener('drop', handleDrop)
    return () => {
      window.removeEventListener('dragenter', handleDragEnter)
      window.removeEventListener('dragleave', handleDragLeave)
      window.removeEventListener('dragover', handleDragOver)
      window.removeEventListener('drop', handleDrop)
    }
  }, [handleDragEnter, handleDragLeave, handleDragOver, handleDrop])

  // ── Upload logic ────────────────────────────────────────────────────────────

  const startUpload = useCallback(async () => {
    if (uploading) return
    setUploading(true)
    setFiles((prev) => prev.map((f) => ({ ...f, status: 'uploading' })))

    try {
      const fileList = files.map((f) => f.file)
      const results: UploadFileResult[] = await uploadApi.uploadFiles(
        fileList,
        (pct) => setOverallPct(pct),
      )

      setFiles((prev) =>
        prev.map((f, i) => {
          const r = results[i]
          if (!r) return { ...f, status: 'ok' }
          return {
            ...f,
            status: r.status,
            reason: r.reason,
          }
        }),
      )
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setFiles((prev) =>
        prev.map((f) => ({ ...f, status: 'error', reason: msg })),
      )
    }

    setOverallPct(100)
    setUploading(false)
    setDone(true)
  }, [uploading, files])

  // Auto-start upload once files are set
  useEffect(() => {
    if (files.length > 0 && !uploading && !done) {
      startUpload()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files])

  const reset = () => {
    setIsOpen(false)
    setFiles([])
    setOverallPct(0)
    setDone(false)
    setUploading(false)
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  const ok    = files.filter((f) => f.status === 'ok').length
  const err   = files.filter((f) => f.status === 'error').length
  const skip  = files.filter((f) => f.status === 'skipped').length

  return (
    <>
      {/* Full-screen drag target overlay */}
      {isDragOver && !isOpen && (
        <div style={styles.dragOverlay}>
          <div style={styles.dragBox}>
            <div style={styles.dragIcon}>🎵</div>
            <p style={styles.dragTitle}>Drop music to upload</p>
            <p style={styles.dragSub}>MP3 · FLAC · OGG · OPUS · M4A · WAV and more</p>
          </div>
        </div>
      )}

      {/* Upload progress panel */}
      {isOpen && (
        <div style={styles.panelBackdrop} onClick={done ? reset : undefined}>
          <div style={styles.panel} onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div style={styles.panelHeader}>
              <span style={styles.panelTitle}>
                {uploading ? 'Uploading…' : done ? 'Upload complete' : 'Ready to upload'}
              </span>
              {done && (
                <button style={styles.closeBtn} onClick={reset}>✕</button>
              )}
            </div>

            {/* Overall progress bar */}
            <div style={styles.progressTrack}>
              <div
                style={{
                  ...styles.progressFill,
                  width: `${overallPct}%`,
                  background: done && err === 0
                    ? 'linear-gradient(90deg,#22c55e,#16a34a)'
                    : 'linear-gradient(90deg,#8b5cf6,#6366f1)',
                }}
              />
            </div>

            {/* Summary */}
            {done && (
              <p style={styles.summary}>
                {ok > 0 && <span style={{ color: '#4ade80' }}>✓ {ok} added </span>}
                {skip > 0 && <span style={{ color: '#facc15' }}>⊘ {skip} skipped </span>}
                {err > 0 && <span style={{ color: '#f87171' }}>✕ {err} failed</span>}
              </p>
            )}

            {/* File list */}
            <div style={styles.fileList}>
              {files.map((f, i) => (
                <div key={i} style={styles.fileRow}>
                  <span style={styles.fileIcon}>
                    {f.status === 'ok'      ? '✓'
                    : f.status === 'error'   ? '✕'
                    : f.status === 'skipped' ? '⊘'
                    :                         '⏳'}
                  </span>
                  <span
                    style={{
                      ...styles.fileName,
                      color: f.status === 'ok'      ? '#4ade80'
                           : f.status === 'error'   ? '#f87171'
                           : f.status === 'skipped' ? '#facc15'
                           : '#a1a1aa',
                    }}
                    title={f.reason}
                  >
                    {f.file.name}
                    {f.reason && <span style={styles.fileReason}> — {f.reason}</span>}
                  </span>
                  <span style={styles.fileSize}>
                    {(f.file.size / 1024 / 1024).toFixed(1)} MB
                  </span>
                </div>
              ))}
            </div>

            {done && (
              <p style={styles.hint}>Click outside or ✕ to close</p>
            )}
          </div>
        </div>
      )}
    </>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles: Record<string, React.CSSProperties> = {
  dragOverlay: {
    position: 'fixed',
    inset: 0,
    zIndex: 9999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(0,0,0,0.7)',
    backdropFilter: 'blur(8px)',
    WebkitBackdropFilter: 'blur(8px)',
    pointerEvents: 'none',
  },
  dragBox: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 12,
    padding: '48px 64px',
    borderRadius: 24,
    border: '2px dashed rgba(139,92,246,0.7)',
    background: 'rgba(139,92,246,0.08)',
    boxShadow: '0 0 60px rgba(139,92,246,0.3)',
  },
  dragIcon: {
    fontSize: 56,
    lineHeight: 1,
  },
  dragTitle: {
    fontSize: 24,
    fontWeight: 700,
    color: '#f1f5f9',
    margin: 0,
  },
  dragSub: {
    fontSize: 13,
    color: '#94a3b8',
    margin: 0,
    letterSpacing: '0.05em',
  },

  panelBackdrop: {
    position: 'fixed',
    inset: 0,
    zIndex: 9998,
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'flex-end',
    padding: 24,
    background: 'rgba(0,0,0,0.5)',
    backdropFilter: 'blur(4px)',
    WebkitBackdropFilter: 'blur(4px)',
  },
  panel: {
    width: 420,
    maxWidth: '100vw',
    maxHeight: '70vh',
    display: 'flex',
    flexDirection: 'column',
    background: 'rgba(18,18,24,0.97)',
    border: '1px solid rgba(139,92,246,0.3)',
    borderRadius: 16,
    boxShadow: '0 24px 80px rgba(0,0,0,0.7), 0 0 40px rgba(139,92,246,0.15)',
    overflow: 'hidden',
  },
  panelHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '14px 18px',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
  },
  panelTitle: {
    fontSize: 14,
    fontWeight: 600,
    color: '#e2e8f0',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#64748b',
    fontSize: 16,
    cursor: 'pointer',
    padding: '2px 6px',
    borderRadius: 6,
    lineHeight: 1,
    transition: 'color 0.15s',
  },
  progressTrack: {
    height: 3,
    background: 'rgba(255,255,255,0.06)',
  },
  progressFill: {
    height: '100%',
    transition: 'width 0.3s ease, background 0.3s',
    borderRadius: 3,
  },
  summary: {
    fontSize: 13,
    padding: '10px 18px 0',
    margin: 0,
    display: 'flex',
    gap: 12,
    flexWrap: 'wrap',
  },
  fileList: {
    overflowY: 'auto',
    flex: 1,
    padding: '8px 0',
  },
  fileRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 18px',
    fontSize: 13,
  },
  fileIcon: {
    fontSize: 12,
    flexShrink: 0,
    width: 16,
    textAlign: 'center',
  },
  fileName: {
    flex: 1,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  fileReason: {
    opacity: 0.6,
    fontStyle: 'italic',
  },
  fileSize: {
    flexShrink: 0,
    color: '#475569',
    fontSize: 11,
  },
  hint: {
    textAlign: 'center',
    fontSize: 12,
    color: '#475569',
    padding: '8px 18px 14px',
    margin: 0,
  },
}
