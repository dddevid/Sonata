import os
import threading
import logging
from mutagen import File as MutagenFile
from django.utils import timezone
from .models import MusicFolder, Song, Artist, Album, Genre, ScanStatus
from .metadata import download_artist_image

AUDIO_EXTENSIONS = {
    '.mp3', '.flac', '.ogg', '.oga', '.opus', '.m4a', '.mp4', '.aac',
    '.wav', '.aiff', '.aif', '.wma', '.alac', '.ape',
}

class Scanner:
    def __init__(self):
        self.is_scanning = False
        self.count = 0
        self.lock = threading.Lock()

    def scan_folders(self, folders):
        with self.lock:
            self.is_scanning = True
            self.count = 0
            scan_status = ScanStatus.get()
            scan_status.is_scanning = True
            scan_status.count = 0
            scan_status.folder_count = len(folders)
            scan_status.save()

            for folder_path in folders:
                if not os.path.isdir(folder_path):
                    logging.warning(f"Music folder not found: {folder_path}")
                    continue
                for dirpath, _dirs, filenames in os.walk(folder_path):
                    for filename in filenames:
                        ext = os.path.splitext(filename)[1].lower()
                        if ext not in AUDIO_EXTENSIONS:
                            continue
                        full_path = os.path.join(dirpath, filename)
                        try:
                            self.process_file(full_path, folder_path)
                            self.count += 1
                        except Exception as e:
                            logging.warning(f"Could not scan {full_path}: {e}")

            scan_status.is_scanning = False
            scan_status.count = self.count
            scan_status.last_scan = timezone.now()
            scan_status.save()
            self.is_scanning = False

    def process_file(self, path, folder_path):
        audio = MutagenFile(path, easy=True)
        if audio is None:
            return
        def tag(key, default=''):
            val = audio.tags.get(key) if audio.tags else None
            return str(val[0]).strip() if val else default
        title = tag('title') or os.path.splitext(os.path.basename(path))[0]
        artist_name = tag('artist') or 'Unknown Artist'
        album_name = tag('album') or 'Unknown Album'
        genre_name = tag('genre')
        year_str = tag('date') or tag('year')
        track_str = tag('tracknumber')
        disc_str = tag('discnumber')
        year = int(year_str.split('-')[0]) if year_str and year_str.split('-')[0].isdigit() else None
        track = int(track_str.split('/')[0]) if track_str and track_str.split('/')[0].isdigit() else None
        disc = int(disc_str.split('/')[0]) if disc_str and disc_str.split('/')[0].isdigit() else None
        duration = int(audio.info.length) if hasattr(audio, 'info') and audio.info else 0
        bit_rate = int(getattr(audio.info, 'bitrate', 0) / 1000) if hasattr(audio, 'info') and audio.info else 0
        size = os.path.getsize(path)
        suffix = os.path.splitext(path)[1].lstrip('.').lower()
        genre = None
        if genre_name:
            genre, _ = Genre.objects.get_or_create(name=genre_name)
        artist, created = Artist.objects.get_or_create(name=artist_name)
        if created or (artist.name != 'Unknown Artist' and not artist.image_path):
            download_artist_image(artist)
        album, _ = Album.objects.get_or_create(
            name=album_name,
            artist=artist,
            defaults={'year': year, 'genre': genre},
        )

        # Cover art extraction
        cover_path = album.cover_art_path
        if not cover_path:
            cover_path = self._extract_cover(path, album)
            if cover_path:
                album.cover_art_path = cover_path
                album.save(update_fields=['cover_art_path'])

        Song.objects.update_or_create(
            path=path,
            defaults={
                'title': title,
                'artist': artist,
                'album': album,
                'genre': genre,
                'music_folder': MusicFolder.objects.get_or_create(path=folder_path)[0],
                'track': track,
                'disc_number': disc,
                'year': year,
                'duration': duration,
                'bit_rate': bit_rate,
                'size': size,
                'suffix': suffix,
                'content_type': f'audio/{suffix}',
            },
        )

    def _extract_cover(self, file_path, album):
        """Extract embedded cover art and save as JPEG, return path."""
        try:
            import mutagen
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3
            from mutagen.flac import FLAC
            from mutagen.mp4 import MP4
            from PIL import Image
            import io
            ext = os.path.splitext(file_path)[1].lower()
            cover_data = None
            mime = 'image/jpeg'
            if ext == '.mp3':
                audio = ID3(file_path)
                for key in audio.keys():
                    if key.startswith('APIC'):
                        apic = audio[key]
                        cover_data = apic.data
                        mime = apic.mime
                        break
            elif ext == '.flac':
                audio = FLAC(file_path)
                if audio.pictures:
                    pic = audio.pictures[0]
                    cover_data = pic.data
                    mime = pic.mime
            elif ext in ('.m4a', '.mp4', '.aac'):
                audio = MP4(file_path)
                if 'covr' in audio:
                    cover = audio['covr'][0]
                    cover_data = bytes(cover)
                    mime = 'image/jpeg'
            if cover_data:
                # Save cover to media/album-art/al-<album_id>.jpg
                media_root = getattr(album, 'media_root', None) or os.environ.get('MEDIA_ROOT', './media')
                art_dir = os.path.join(media_root, 'album-art')
                os.makedirs(art_dir, exist_ok=True)
                art_path = os.path.join(art_dir, f'al-{album.pk}.jpg')
                img = Image.open(io.BytesIO(cover_data)).convert('RGB')
                img.save(art_path, format='JPEG', quality=85)
                return art_path
        except Exception as e:
            logging.warning(f"Cover extraction failed for {file_path}: {e}")
        return None
