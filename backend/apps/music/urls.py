from django.urls import path
from . import views

urlpatterns = [
    # Admin / library
    path('folders/', views.music_folders),
    path('folders/<int:folder_id>/', views.music_folder_detail),

    # Scan
    path('scan/start/', views.start_scan),
    path('scan/status/', views.scan_status),
    path('scan/callback/', views.scan_callback),

    # Browse
    path('artists/', views.artists),
    path('artists/<int:artist_id>/', views.artist_detail),
    path('albums/', views.albums),
    path('albums/<int:album_id>/', views.album_detail),
    path('songs/', views.songs),
    path('songs/<int:song_id>/', views.song_detail),

    # Cover art for web UI (JWT auth)
    path('cover-art/<str:art_id>/', views.cover_art_image),

    # Stats
    path('stats/', views.stats),

    # Playlists
    path('playlists/', views.playlists),
    path('playlists/<int:playlist_id>/', views.playlist_detail),
    path('playlists/<int:playlist_id>/songs/', views.playlist_add_songs),

    # Radio
    path('radio/', views.radio_stations),
    path('radio/<int:station_id>/', views.radio_station_detail),

    # Server logs (admin only)
    path('logs/', views.server_logs),
]
