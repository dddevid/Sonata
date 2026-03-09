"""annotation.py — star, unstar, setRating, scrobble"""

import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.subsonic.auth import subsonic_auth
from apps.subsonic.helpers import make_ok, make_error
from apps.music.models import Song, Album, Artist, Starred, UserRating


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def star(request):
    return _toggle_star(request, star=True)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def unstar(request):
    return _toggle_star(request, star=False)


def _toggle_star(request, star):
    p = request.GET if request.method == 'GET' else request.POST
    user = request.subsonic_user

    for song_id in p.getlist('id') or p.getlist('id[]'):
        try:
            song = Song.objects.get(pk=song_id)
            if star:
                Starred.objects.get_or_create(user=user, song=song)
            else:
                Starred.objects.filter(user=user, song=song).delete()
        except (Song.DoesNotExist, ValueError):
            pass

    for album_id in p.getlist('albumId') or p.getlist('albumId[]'):
        try:
            album = Album.objects.get(pk=album_id)
            if star:
                Starred.objects.get_or_create(user=user, album=album)
            else:
                Starred.objects.filter(user=user, album=album).delete()
        except (Album.DoesNotExist, ValueError):
            pass

    for artist_id in p.getlist('artistId') or p.getlist('artistId[]'):
        try:
            artist = Artist.objects.get(pk=artist_id)
            if star:
                Starred.objects.get_or_create(user=user, artist=artist)
            else:
                Starred.objects.filter(user=user, artist=artist).delete()
        except (Artist.DoesNotExist, ValueError):
            pass

    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def set_rating(request):
    p = request.GET if request.method == 'GET' else request.POST
    item_id = p.get('id')
    rating = p.get('rating', '0')

    if not item_id:
        return make_error(request, 10, 'Required parameter missing: id')

    try:
        rating_int = int(rating)
    except ValueError:
        return make_error(request, 10, 'Invalid rating value')

    user = request.subsonic_user

    try:
        song = Song.objects.get(pk=item_id)
        if rating_int == 0:
            UserRating.objects.filter(user=user, song=song).delete()
        else:
            UserRating.objects.update_or_create(user=user, song=song, defaults={'rating': rating_int})
    except (Song.DoesNotExist, ValueError):
        try:
            album = Album.objects.get(pk=item_id)
            if rating_int == 0:
                UserRating.objects.filter(user=user, album=album).delete()
            else:
                UserRating.objects.update_or_create(user=user, album=album, defaults={'rating': rating_int})
        except (Album.DoesNotExist, ValueError):
            pass

    return make_ok(request)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
@subsonic_auth
def scrobble(request):
    p = request.GET if request.method == 'GET' else request.POST
    song_id = p.get('id')
    submission = p.get('submission', 'true').lower() == 'true'

    if not song_id:
        return make_error(request, 10, 'Required parameter missing: id')

    if submission:
        try:
            song = Song.objects.get(pk=song_id)
            song.play_count += 1
            from django.utils import timezone
            song.last_played = timezone.now()
            song.save(update_fields=['play_count', 'last_played'])
        except (Song.DoesNotExist, ValueError):
            pass

    return make_ok(request)
