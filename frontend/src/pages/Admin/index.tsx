import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, FolderOpen, BarChart2, RefreshCw, Plus, Trash2, Edit2, X, Check, Loader2, Terminal, ChevronDown } from 'lucide-react'
import { adminApi } from '@/api'

type Tab = 'overview' | 'users' | 'libraries' | 'logs'

// ---------- Overview ----------
function Overview() {
  const { data: stats } = useQuery({ queryKey: ['admin', 'stats'], queryFn: adminApi.stats })

  const cards = [
    { label: 'Artists', value: stats?.artists ?? '—', icon: '🎤' },
    { label: 'Albums', value: stats?.albums ?? '—', icon: '💿' },
    { label: 'Songs', value: stats?.songs ?? '—', icon: '🎵' },
    { label: 'Genres', value: stats?.genres ?? '—', icon: '🎸' },
    { label: 'Users', value: stats?.users ?? '—', icon: '👥' },
    { label: 'Folders', value: stats?.folders ?? '—', icon: '📁' },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((c) => (
        <div key={c.label} className="bg-elevated border border-border rounded-xl p-5">
          <span className="text-2xl">{c.icon}</span>
          <p className="text-2xl font-bold text-text-primary mt-3">{c.value.toLocaleString()}</p>
          <p className="text-xs text-text-muted mt-1">{c.label}</p>
        </div>
      ))}
    </div>
  )
}

// ---------- Users ----------
function UsersTab() {
  const [showCreate, setShowCreate] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [form, setForm] = useState({ username: '', email: '', password: '', role: 'user' })
  const [editForm, setEditForm] = useState<{role: 'admin' | 'user'}>({ role: 'user' })
  const qc = useQueryClient()

  const { data: users = [] } = useQuery({ queryKey: ['admin', 'users'], queryFn: adminApi.listUsers })

  const createMutation = useMutation({
    mutationFn: () => adminApi.createUser({ username: form.username, email: form.email, password: form.password, role: form.role }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'users'] }); setShowCreate(false); setForm({ username: '', email: '', password: '', role: 'user' }) },
  })

  const updateMutation = useMutation({
    mutationFn: (id: number) => adminApi.updateUser(id, { role: editForm.role }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'users'] }); setEditId(null) },
  })

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'users'] }),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-text-secondary">{users.length} user{users.length !== 1 ? 's' : ''}</p>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1.5 text-sm bg-primary-light hover:bg-primary text-white px-3 py-1.5 rounded-lg transition-colors"
        >
          <Plus size={14} /> Add User
        </button>
      </div>

      {showCreate && (
        <div className="bg-elevated border border-border rounded-xl p-4 mb-4 space-y-3">
          <p className="text-sm font-medium text-text-primary">New User</p>
          <div className="grid grid-cols-2 gap-3">
            <input
              type="text"
              placeholder="Username"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light"
            />
            <input
              type="email"
              placeholder="Email (optional)"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light"
            />
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary-light"
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowCreate(false)} className="text-sm text-text-secondary hover:text-text-primary px-3 py-1.5 rounded-lg hover:bg-border transition-colors">
              Cancel
            </button>
            <button
              onClick={() => createMutation.mutate()}
              disabled={!form.username || !form.password || createMutation.isPending}
              className="flex items-center gap-1.5 text-sm bg-primary-light hover:bg-primary disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition-colors"
            >
              {createMutation.isPending && <Loader2 size={12} className="animate-spin" />} Create
            </button>
          </div>
        </div>
      )}

      <div className="bg-elevated border border-border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-3 text-xs text-text-muted font-medium">Username</th>
              <th className="text-left px-4 py-3 text-xs text-text-muted font-medium">Role</th>
              <th className="text-left px-4 py-3 text-xs text-text-muted font-medium">Joined</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {users.map((user: any, i: number) => (
              <tr key={user.id} className={`${i < users.length - 1 ? 'border-b border-border' : ''}`}>
                <td className="px-4 py-3 text-text-primary font-medium">{user.username}</td>
                <td className="px-4 py-3">
                  {editId === user.id ? (
                    <select
                      value={editForm.role}
                      onChange={(e) => setEditForm({ role: e.target.value as 'admin' | 'user' })}
                      className="bg-surface border border-border rounded px-2 py-1 text-xs text-text-primary focus:outline-none"
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  ) : (
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${user.role === 'admin' ? 'bg-primary/20 text-primary-light' : 'bg-elevated text-text-muted border border-border'}`}>
                      {user.role}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-text-muted text-xs">
                  {user.date_joined ? new Date(user.date_joined).toLocaleDateString() : '—'}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 justify-end">
                    {editId === user.id ? (
                      <>
                        <button onClick={() => updateMutation.mutate(user.id)} className="p-1 text-green-400 hover:text-green-300 transition-colors" title="Save">
                          <Check size={14} />
                        </button>
                        <button onClick={() => setEditId(null)} className="p-1 text-text-muted hover:text-text-primary transition-colors" title="Cancel">
                          <X size={14} />
                        </button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => { setEditId(user.id); setEditForm({ role: user.role as 'admin' | 'user' }) }} className="p-1 text-text-muted hover:text-text-primary transition-colors" title="Edit">
                          <Edit2 size={14} />
                        </button>
                        <button onClick={() => deleteMutation.mutate(user.id)} className="p-1 text-text-muted hover:text-red-400 transition-colors" title="Delete">
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ---------- Libraries ----------
function LibrariesTab() {
  const [showAdd, setShowAdd] = useState(false)
  const [newPath, setNewPath] = useState('')
  const [newName, setNewName] = useState('')
  const qc = useQueryClient()

  const { data: folders = [] } = useQuery({ queryKey: ['admin', 'folders'], queryFn: adminApi.listFolders })
  const { data: scanData, refetch: refetchScan } = useQuery({
    queryKey: ['admin', 'scan'],
    queryFn: adminApi.scanStatus,
    refetchInterval: (q) => q.state.data?.is_scanning ? 3000 : false,
  })

  const createFolder = useMutation({
    mutationFn: () => adminApi.createFolder({ name: newName, path: newPath }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin', 'folders'] }); setShowAdd(false); setNewPath(''); setNewName('') },
  })

  const deleteFolder = useMutation({
    mutationFn: adminApi.deleteFolder,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'folders'] }),
  })

  const startScan = useMutation({
    mutationFn: adminApi.startScan,
    onSuccess: () => refetchScan(),
  })

  const isScanning = scanData?.is_scanning ?? false

  return (
    <div className="space-y-6">
      {/* Scan Status */}
      <div className="bg-elevated border border-border rounded-xl p-5 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-text-primary">Library Scan</p>
          {isScanning ? (
            <p className="text-xs text-text-muted mt-1">
              Scanning… {scanData?.scanned_files ?? 0} files processed
            </p>
          ) : (
            <p className="text-xs text-text-muted mt-1">
              {scanData?.last_scan ? `Last scan: ${new Date(scanData.last_scan).toLocaleString()}` : 'Never scanned'}
              {scanData?.total_files != null && ` · ${scanData.total_files} files`}
            </p>
          )}
        </div>
        <button
          onClick={() => startScan.mutate()}
          disabled={isScanning}
          className="flex items-center gap-2 bg-primary-light hover:bg-primary disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          {isScanning ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          {isScanning ? 'Scanning…' : 'Start Scan'}
        </button>
      </div>

      {/* Folders */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-text-primary">Music Folders</p>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="flex items-center gap-1.5 text-sm bg-elevated hover:bg-border border border-border text-text-primary px-3 py-1.5 rounded-lg transition-colors"
          >
            <Plus size={14} /> Add Folder
          </button>
        </div>

        {showAdd && (
          <div className="bg-elevated border border-border rounded-xl p-4 mb-3 space-y-3">
            <input
              type="text"
              placeholder="Display name (e.g. Music)"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light"
            />
            <input
              type="text"
              placeholder="Absolute path (e.g. /mnt/music)"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-primary-light"
            />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowAdd(false)} className="text-sm text-text-secondary hover:text-text-primary px-3 py-1.5 rounded-lg hover:bg-border transition-colors">Cancel</button>
              <button
                onClick={() => createFolder.mutate()}
                disabled={!newName || !newPath || createFolder.isPending}
                className="text-sm bg-primary-light hover:bg-primary disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition-colors"
              >
                Add
              </button>
            </div>
          </div>
        )}

        {folders.length === 0 ? (
          <div className="text-center py-10 text-text-muted text-sm">No folders configured</div>
        ) : (
          <div className="bg-elevated border border-border rounded-xl overflow-hidden">
            {folders.map((folder: any, i: number) => (
              <div key={folder.id} className={`flex items-center gap-4 px-4 py-3 ${i < folders.length - 1 ? 'border-b border-border' : ''}`}>
                <FolderOpen size={16} className="text-text-muted flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-text-primary">{folder.name}</p>
                  <p className="text-xs text-text-muted truncate">{folder.path}</p>
                </div>
                <button onClick={() => deleteFolder.mutate(folder.id)} className="p-1.5 text-text-muted hover:text-red-400 transition-colors" title="Remove">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ---------- Logs ----------
const LEVEL_STYLES: Record<string, string> = {
  DEBUG:    'text-text-muted',
  INFO:     'text-blue-400',
  WARNING:  'text-yellow-400',
  ERROR:    'text-red-400',
  CRITICAL: 'text-red-500 font-bold',
}

function LogsTab() {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [filter, setFilter] = useState('')

  const { data, isFetching } = useQuery({
    queryKey: ['admin', 'logs'],
    queryFn: () => adminApi.logs(500),
    refetchInterval: 3000,
  })

  const logs = (data?.logs ?? []).filter(l =>
    !filter || l.msg.toLowerCase().includes(filter.toLowerCase()) || l.level.toLowerCase().includes(filter.toLowerCase()) || l.logger.toLowerCase().includes(filter.toLowerCase())
  )

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 40)
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Filter logs…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="flex-1 bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-primary/60"
        />
        <span className="text-xs text-text-muted whitespace-nowrap">{logs.length} entries</span>
        {isFetching && <Loader2 size={14} className="animate-spin text-text-muted" />}
        <button
          onClick={() => setAutoScroll(true)}
          title="Scroll to bottom"
          className={`p-1.5 rounded-md transition-colors ${autoScroll ? 'text-primary-light bg-primary/10' : 'text-text-muted hover:text-text-primary hover:bg-elevated'}`}
        >
          <ChevronDown size={16} />
        </button>
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="bg-black/60 border border-border rounded-xl p-4 h-[480px] overflow-y-auto font-mono text-xs space-y-0.5 scrollbar-thin scrollbar-thumb-border"
      >
        {logs.length === 0 ? (
          <p className="text-text-muted text-center pt-10">No log entries yet — they'll appear as the server runs.</p>
        ) : (
          logs.map((entry, i) => (
            <div key={i} className="flex gap-2 leading-5 hover:bg-white/5 rounded px-1">
              <span className="text-text-muted shrink-0">{entry.ts}</span>
              <span className={`shrink-0 w-14 text-right uppercase text-[10px] font-semibold leading-5 ${LEVEL_STYLES[entry.level] ?? 'text-text-secondary'}`}>
                {entry.level}
              </span>
              <span className="text-text-muted/60 shrink-0 truncate max-w-[140px]" title={entry.logger}>{entry.logger}</span>
              <span className="text-text-primary/90 break-all">{entry.msg}</span>
            </div>
          ))
        )}
      </div>
      <p className="text-xs text-text-muted">Auto-refreshes every 3 s · last 500 entries</p>
    </div>
  )
}

// ---------- Main Admin Page ----------
export default function Admin() {
  const [tab, setTab] = useState<Tab>('overview')

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'overview', label: 'Overview', icon: <BarChart2 size={15} /> },
    { key: 'users', label: 'Users', icon: <Users size={15} /> },
    { key: 'libraries', label: 'Libraries', icon: <FolderOpen size={15} /> },
    { key: 'logs', label: 'Logs', icon: <Terminal size={15} /> },
  ]

  return (
    <div className="p-6 animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary">Admin Panel</h1>
        <p className="text-sm text-text-secondary mt-1">Manage your Sonata server</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border mb-6">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === t.key
                ? 'border-primary-light text-primary-light'
                : 'border-transparent text-text-muted hover:text-text-primary'
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && <Overview />}
      {tab === 'users' && <UsersTab />}
      {tab === 'libraries' && <LibrariesTab />}
      {tab === 'logs' && <LogsTab />}
    </div>
  )
}
