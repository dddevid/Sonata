from django.contrib import admin
from .models import (
    MusicFolder, Genre, Artist, Album, Song,
    Playlist, InternetRadioStation, ScanStatus,
)


@admin.register(MusicFolder)
class MusicFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'enabled', 'created')
    list_filter = ('enabled',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'song_count', 'album_count')
    search_fields = ('name',)


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'album_count', 'created')
    search_fields = ('name',)


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('name', 'artist', 'year', 'song_count', 'duration', 'created')
    list_filter = ('year', 'genre')
    search_fields = ('name', 'artist__name')
    raw_id_fields = ('artist', 'genre')


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'album', 'track', 'duration', 'suffix', 'play_count')
    list_filter = ('suffix', 'genre')
    search_fields = ('title', 'artist__name', 'album__name')
    raw_id_fields = ('artist', 'album', 'genre', 'music_folder')


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'public', 'created')


@admin.register(InternetRadioStation)
class RadioAdmin(admin.ModelAdmin):
    list_display = ('name', 'stream_url')


@admin.register(ScanStatus)
class ScanStatusAdmin(admin.ModelAdmin):
    list_display = ('is_scanning', 'count', 'folder_count', 'last_scan')
