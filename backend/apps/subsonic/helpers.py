"""
OpenSubsonic response helpers.

Supports both JSON (f=json) and XML (f=xml, default) output formats.
"""

import xml.etree.ElementTree as ET
from django.conf import settings
from django.http import HttpResponse, JsonResponse

SUBSONIC_NS = 'http://subsonic.org/restapi'
API_VERSION = getattr(settings, 'SUBSONIC_API_VERSION', '1.16.1')
SERVER_NAME = getattr(settings, 'SERVER_NAME', 'Sonata')
SERVER_VERSION = getattr(settings, 'SERVER_VERSION', '1.0.0')


# ── Response constructors ──────────────────────────────────────────────────────

def _base_attrs():
    return {
        'status': 'ok',
        'version': API_VERSION,
        'type': SERVER_NAME,
        'serverVersion': SERVER_VERSION,
        'openSubsonic': True,
    }


def ok_json(data: dict = None) -> JsonResponse:
    body = _base_attrs()
    if data:
        body.update(data)
    return JsonResponse({'subsonic-response': body})


def error_json(code: int, message: str) -> JsonResponse:
    body = _base_attrs()
    body['status'] = 'failed'
    body['error'] = {'code': code, 'message': message}
    return JsonResponse({'subsonic-response': body}, status=200)


def ok_xml(data_builder=None) -> HttpResponse:
    root = ET.Element('subsonic-response', {
        'xmlns': SUBSONIC_NS,
        'status': 'ok',
        'version': API_VERSION,
        'type': SERVER_NAME,
        'serverVersion': SERVER_VERSION,
        'openSubsonic': 'true',
    })
    if data_builder:
        data_builder(root)
    return HttpResponse(
        '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(root, encoding='unicode'),
        content_type='application/xml; charset=utf-8',
    )


def error_xml(code: int, message: str) -> HttpResponse:
    root = ET.Element('subsonic-response', {
        'xmlns': SUBSONIC_NS,
        'status': 'failed',
        'version': API_VERSION,
        'type': SERVER_NAME,
        'serverVersion': SERVER_VERSION,
        'openSubsonic': 'true',
    })
    ET.SubElement(root, 'error', {'code': str(code), 'message': message})
    return HttpResponse(
        '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(root, encoding='unicode'),
        content_type='application/xml; charset=utf-8',
    )


# ── Unified response helper used by view functions ────────────────────────────

def make_ok(request, data: dict = None, xml_builder=None):
    """Return ok response in the format requested by the client (f param)."""
    fmt = _get_format(request)
    if fmt == 'json' or fmt == 'jsonp':
        return ok_json(data or {})
    return ok_xml(xml_builder)


def make_error(request, code: int, message: str):
    """Return error response in the format requested by the client."""
    fmt = _get_format(request)
    if fmt == 'json' or fmt == 'jsonp':
        return error_json(code, message)
    return error_xml(code, message)


def _get_format(request) -> str:
    return (
        request.GET.get('f')
        or request.POST.get('f')
        or 'xml'
    ).lower()


# ── XML serialisation helpers ─────────────────────────────────────────────────

def song_to_xml(song, elem: ET.Element, starred_ids=None, ratings=None):
    attrs = _song_attrs(song, starred_ids, ratings)
    ET.SubElement(elem, 'song', attrs)


def song_to_dict(song, starred_ids=None, ratings=None) -> dict:
    return _song_attrs(song, starred_ids, ratings)


def _song_attrs(song, starred_ids=None, ratings=None) -> dict:
    d = {
        'id': str(song.pk),
        'parent': str(song.album_id),
        'title': song.title,
        'album': song.album.name if song.album_id else '',
        'artist': song.artist.name if song.artist_id else '',
        'isDir': 'false',
        'coverArt': song.cover_art_id(),
        'created': song.created.isoformat(),
        'duration': str(song.duration),
        'bitRate': str(song.bit_rate),
        'size': str(song.size),
        'suffix': song.suffix,
        'contentType': song.content_type,
        'isVideo': 'false',
        'path': song.path,
        'albumId': str(song.album_id),
        'artistId': str(song.artist_id),
        'type': 'music',
        'playCount': str(song.play_count),
    }
    if song.track:
        d['track'] = str(song.track)
    if song.disc_number:
        d['discNumber'] = str(song.disc_number)
    if song.year:
        d['year'] = str(song.year)
    if song.genre_id:
        d['genre'] = song.genre.name
    if starred_ids and song.pk in starred_ids:
        d['starred'] = song.created.isoformat()
    if ratings and song.pk in ratings:
        d['userRating'] = str(ratings[song.pk])
    return d


def album_to_dict(album, starred_ids=None) -> dict:
    d = {
        'id': str(album.pk),
        'name': album.name,
        'title': album.name,
        'album': album.name,
        'artist': album.artist.name if album.artist_id else '',
        'artistId': str(album.artist_id),
        'coverArt': album.cover_art_id(),
        'songCount': str(album.song_count),
        'duration': str(album.duration),
        'created': album.created.isoformat(),
        'isDir': 'true',
    }
    if album.year:
        d['year'] = str(album.year)
    if album.genre_id:
        d['genre'] = album.genre.name
    if starred_ids and album.pk in starred_ids:
        d['starred'] = album.created.isoformat()
    return d


def artist_to_dict(artist, starred_ids=None) -> dict:
    d = {
        'id': str(artist.pk),
        'name': artist.name,
        'albumCount': str(artist.album_count),
    }
    if artist.image_url:
        d['artistImageUrl'] = artist.image_url
    if starred_ids and artist.pk in starred_ids:
        d['starred'] = artist.created.isoformat()
    return d
