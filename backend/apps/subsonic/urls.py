"""
OpenSubsonic URL configuration.
All endpoints are accessible with or without the .view suffix.
"""

from django.urls import re_path
from .views import system, browsing, lists, search, playlists, media, annotation, users, scan, internet_radio, bookmarks, sharing


def _path(name, view):
    """Match endpoint with or without .view suffix."""
    return re_path(rf'^{name}(?:\.view)?/?$', view, name=name)


urlpatterns = [
    # System
    _path('ping', system.ping),
    _path('getLicense', system.get_license),
    _path('getOpenSubsonicExtensions', system.get_extensions),

    # Browsing
    _path('getMusicFolders', browsing.get_music_folders),
    _path('getIndexes', browsing.get_indexes),
    _path('getMusicDirectory', browsing.get_music_directory),
    _path('getArtists', browsing.get_artists),
    _path('getArtist', browsing.get_artist),
    _path('getAlbum', browsing.get_album),
    _path('getSong', browsing.get_song),
    _path('getGenres', browsing.get_genres),
    _path('getArtistInfo', browsing.get_artist_info),
    _path('getArtistInfo2', browsing.get_artist_info2),
    _path('getAlbumInfo', browsing.get_album_info),
    _path('getAlbumInfo2', browsing.get_album_info2),
    _path('getSimilarSongs', browsing.get_similar_songs),
    _path('getSimilarSongs2', browsing.get_similar_songs2),
    _path('getTopSongs', browsing.get_top_songs),
    _path('getVideos', system.ping),  # stub

    # Album/Song lists
    _path('getAlbumList', lists.get_album_list),
    _path('getAlbumList2', lists.get_album_list2),
    _path('getRandomSongs', lists.get_random_songs),
    _path('getSongsByGenre', lists.get_songs_by_genre),
    _path('getNowPlaying', lists.get_now_playing),
    _path('getStarred', lists.get_starred),
    _path('getStarred2', lists.get_starred2),

    # Search
    _path('search2', search.search2),
    _path('search3', search.search3),

    # Playlists
    _path('getPlaylists', playlists.get_playlists),
    _path('getPlaylist', playlists.get_playlist),
    _path('createPlaylist', playlists.create_playlist),
    _path('updatePlaylist', playlists.update_playlist),
    _path('deletePlaylist', playlists.delete_playlist),

    # Media
    _path('stream', media.stream),
    _path('download', media.download),
    _path('hls', media.hls),
    _path('getCoverArt', media.get_cover_art),
    _path('getLyrics', media.get_lyrics),
    _path('getAvatar', media.get_avatar),

    # Annotation
    _path('star', annotation.star),
    _path('unstar', annotation.unstar),
    _path('setRating', annotation.set_rating),
    _path('scrobble', annotation.scrobble),

    # Users
    _path('getUser', users.get_user),
    _path('getUsers', users.get_users),
    _path('createUser', users.create_user),
    _path('updateUser', users.update_user),
    _path('changePassword', users.change_password),
    _path('deleteUser', users.delete_user),

    # Scan
    _path('getScanStatus', scan.get_scan_status),
    _path('startScan', scan.start_scan),

    # Internet Radio
    _path('getInternetRadioStations', internet_radio.get_stations),
    _path('createInternetRadioStation', internet_radio.create_station),
    _path('updateInternetRadioStation', internet_radio.update_station),
    _path('deleteInternetRadioStation', internet_radio.delete_station),

    # Bookmarks & Play Queue
    _path('getBookmarks', bookmarks.get_bookmarks),
    _path('createBookmark', bookmarks.create_bookmark),
    _path('deleteBookmark', bookmarks.delete_bookmark),
    _path('getPlayQueue', bookmarks.get_play_queue),
    _path('savePlayQueue', bookmarks.save_play_queue),

    # Sharing
    _path('getShares', sharing.get_shares),
    _path('createShare', sharing.create_share),
    _path('updateShare', sharing.update_share),
    _path('deleteShare', sharing.delete_share),
]
