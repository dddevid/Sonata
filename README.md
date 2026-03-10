# Sonata Music Server

> [!WARNING]
> This project is in alpha: expect bugs, frequent changes, and incomplete features. Use at your own risk!

A self-hosted music streaming server fully compatible with the **OpenSubsonic API**, featuring a modern React web UI and a high-performance Go-based media scanner.

## Features

- Full **OpenSubsonic API** (v1.16.1) compatibility — works with Symfonium, Tempo, DSub, Ultrasonic, etc.
- Modern, minimal dark web UI inspired by Navidrome
- Admin panel: user management, music libraries, scan control
- **First registered user automatically becomes admin**
- High-performance file scanner written in **Go**
- On-the-fly audio transcoding via **FFmpeg** (Go service)
- Range-request streaming with cover art extraction
- Playlist management, starred items, ratings, scrobble, bookmarks

## Architecture

```
┌──────────────┐     OpenSubsonic     ┌─────────────┐
│  Any Subsonic│ ──────────────────►  │             │
│    Client    │                      │   Django    │
└──────────────┘                      │   Backend   │
                                      │  (Port 8000)│
┌──────────────┐     REST /api/*      │             │
│  React Web   │ ──────────────────►  │             │
│      UI      │                      └──────┬──────┘
└──────────────┘                             │ Internal API
                                      ┌──────▼──────┐
                                      │  Go Scanner │
                                      │ (Port 4040) │
                                      └─────────────┘
```

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3.11 + Django 4.2 + DRF     |
| Scanner    | Go 1.21 (gin, dhowden/tag, mutagen) |
| Frontend   | React 18 + TypeScript + Tailwind    |
| Database   | SQLite (dev) / PostgreSQL (prod)    |

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
```bash
cd scanner
go build -o bin/sonata-scanner .
./bin/sonata-scanner
```

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

## Environment Variables

See `backend/.env.example` for all available configuration options.

## License

This project is open source and available under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)** License. See the [LICENSE](LICENSE) file for details.
