# Sonata Music Server

> [!WARNING]
> This project is in alpha: expect bugs, frequent changes, and incomplete features. Use at your own risk!

A self-hosted music streaming server fully compatible with the **OpenSubsonic API**, featuring a modern React web UI and a Python-based media scanner with mutagen for metadata extraction.

## Features

- Full **OpenSubsonic API** (v1.16.1) compatibility — works with Symfonium, Tempo, DSub, Ultrasonic, etc.
- Modern, minimal dark web UI inspired by Navidrome
- Admin panel: user management, music libraries, scan control
- **First registered user automatically becomes admin**
- High-performance file scanner written in **Python** with mutagen
- On-the-fly audio transcoding via **FFmpeg**
- Range-request streaming with cover art extraction
- Playlist management, starred items, ratings, scrobble, bookmarks
- **LDAP authentication** support with automatic user provisioning

## Architecture

```
┌──────────────┐     OpenSubsonic     ┌─────────────┐
│  Any Subsonic│ ──────────────────►  │             │
│    Client    │                      │   Django    │
└──────────────┘                      │   Backend   │
                                      │  (Port 8000)│
┌──────────────┐     REST /api/*      │             │
│  React Web   │ ──────────────────►  │   +Scanner  │
│      UI      │                      │   (Python)  │
└──────────────┘                      └─────────────┘
```

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.11 + Django 4.2 + DRF      |
| Scanner    | Python + mutagen (integrated)       |
| Frontend   | React 18 + TypeScript + Tailwind    |
| Database   | SQLite (dev)                        |
| Auth       | Local + JWT + LDAP (optional)       |

## Quick Start

```bash
# Clone and run setup
chmod +x setup.sh
./setup.sh
```

Then open **http://localhost:5173** — the first user you register becomes admin.

## Manual Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Scanner
The scanner is integrated into the Django backend. No separate service needed.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## OpenSubsonic API

All endpoints available at `/rest/` (with or without `.view` suffix):

- **System**: `ping`, `getLicense`, `getOpenSubsonicExtensions`
- **Browsing**: `getMusicFolders`, `getIndexes`, `getArtists`, `getArtist`, `getAlbum`, `getSong`, `getGenres`, `getMusicDirectory`
- **Search**: `search2`, `search3`
- **Lists**: `getAlbumList`, `getAlbumList2`, `getRandomSongs`, `getSongsByGenre`, `getStarred`, `getStarred2`
- **Playlists**: `getPlaylists`, `getPlaylist`, `createPlaylist`, `updatePlaylist`, `deletePlaylist`
- **Media**: `stream`, `download`, `getCoverArt`, `getAvatar`, `getLyrics`
- **Annotation**: `star`, `unstar`, `setRating`, `scrobble`
- **Users**: `getUser`, `getUsers`, `createUser`, `updateUser`, `changePassword`, `deleteUser`
- **Bookmarks**: `getBookmarks`, `createBookmark`, `deleteBookmark`, `getPlayQueue`, `savePlayQueue`
- **Radio**: `getInternetRadioStations`, `createInternetRadioStation`, `updateInternetRadioStation`, `deleteInternetRadioStation`
- **Sharing**: `getShares`, `createShare`, `updateShare`, `deleteShare`
- **Scan**: `getScanStatus`, `startScan`

## Configuration

Sonata uses a **database-first configuration system**. All settings (except database connection) are stored in the database and editable via the Admin UI.

### How it works

1. **Auto-generated security keys**: On first startup, the server automatically generates and securely stores:
   - `SECRET_KEY` (Django security key)
   - `SUBSONIC_ENCRYPTION_KEY` (for password encryption)

2. **Admin UI configuration**: After logging in as admin, go to **Admin → Server Settings** to configure:
   - Server name, debug mode
   - User registration settings
   - CORS origins
   - JWT token lifetimes
   - Rate limiting
   - LDAP authentication
   - Regenerate security keys

### Environment Variables (Optional)

Only set these if you need to override defaults:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection (optional) | `sqlite:///db.sqlite3` |
| `SECRET_KEY` | Override auto-generated key | *(auto-generated)* |

### LDAP Authentication

LDAP can be configured via the Admin UI (Server Settings → LDAP). No `.env` file needed!

**Quick setup:**
1. Log in as admin
2. Go to Admin → Server Settings
3. Enable LDAP and fill in your server details:
   - Server URI: `ldap://ldap.example.com`
   - Bind DN: Service account for searching
   - User Search Base: `ou=users,dc=example,dc=com`
4. Save and LDAP users can immediately log in

**System dependencies** (if using LDAP):
```bash
# macOS
brew install openldap

# Ubuntu/Debian
sudo apt-get install libldap2-dev libsasl2-dev
```

## License

MIT
