import os
import requests
import logging
from urllib.parse import quote
from django.conf import settings


def _wiki_headers():
    """
    Build headers for Wikimedia API calls.
    Wikimedia requires a descriptive User-Agent.
    """
    app_name = getattr(settings, 'SERVER_NAME', 'Sonata')
    app_version = getattr(settings, 'SERVER_VERSION', '1.0.0')
    contact = os.environ.get('WIKIMEDIA_CONTACT', 'https://github.com/')
    return {
        'User-Agent': f'{app_name}/{app_version} (contact: {contact})'
    }


def fetch_artist_thumbnail_url(artist_name):
    """
    Tries TheAudioDB first, then Wikimedia as a fallback.
    Returns URL string or None.
    """
    if not artist_name or artist_name == 'Unknown Artist':
        return None

    # 1. TheAudioDB (primary source)
    tadb_url = f"https://www.theaudiodb.com/api/v1/json/2/search.php?s={quote(artist_name)}"
    try:
        r = requests.get(tadb_url, timeout=5)
        r.raise_for_status()
        data = r.json()
        artists = data.get('artists')
        if artists:
            thumb = artists[0].get('strArtistThumb')
            if thumb:
                return thumb
    except Exception as e:
        logging.warning(f"TheAudioDB failed for {artist_name}: {e}")

    # 2. Wikimedia (fallback)
    wiki_url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&format=json&prop=pageimages&titles={quote(artist_name)}&pithumbsize=1000"
    )
    try:
        r = requests.get(wiki_url, timeout=5, headers=_wiki_headers())
        r.raise_for_status()
        data = r.json()
        pages = data.get('query', {}).get('pages', {})
        for page_id in pages:
            thumb = pages[page_id].get('thumbnail', {}).get('source')
            if thumb:
                return thumb
    except Exception as e:
        logging.warning(f"Wikimedia failed for {artist_name}: {e}")

    return None

def download_artist_image(artist):
    """
    Fetches thumb URL, downloads it, saves locally, updates artist.
    """
    if artist.image_path and os.path.exists(artist.image_path):
        return artist.image_path

    url = fetch_artist_thumbnail_url(artist.name)
    if not url:
        return None

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        
        media_root = getattr(settings, 'MEDIA_ROOT', './media')
        art_dir = os.path.join(media_root, 'artist-images')
        os.makedirs(art_dir, exist_ok=True)
        
        # Determine extension from URL or content-type
        ext = '.jpg'
        if 'png' in url.lower(): ext = '.png'
        
        file_path = os.path.join(art_dir, f'ar-{artist.pk}{ext}')
        with open(file_path, 'wb') as f:
            f.write(r.content)
            
        artist.image_url = url
        artist.image_path = file_path
        artist.save(update_fields=['image_url', 'image_path'])
        return file_path
    except Exception as e:
        logging.warning(f"Failed to download image for {artist.name}: {e}")
        
    return None
