from rest_framework import serializers
from .models import (
    MusicFolder, Genre, Artist, Album, Song,
    Playlist, PlaylistSong, InternetRadioStation, ScanStatus,
)


class MusicFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MusicFolder
        fields = '__all__'


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = '__all__'


class AlbumSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    genre_name = serializers.CharField(source='genre.name', read_only=True, allow_null=True)

    class Meta:
        model = Album
        fields = '__all__'


class SongSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    album_name = serializers.CharField(source='album.name', read_only=True)
    genre_name = serializers.CharField(source='genre.name', read_only=True, allow_null=True)

    class Meta:
        model = Song
        fields = '__all__'


class PlaylistSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    song_count = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = '__all__'

    def get_song_count(self, obj):
        return obj.entries.count()

    def get_duration(self, obj):
        return sum(e.song.duration for e in obj.entries.select_related('song').all())


class RadioStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternetRadioStation
        fields = '__all__'


class ScanStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanStatus
        fields = '__all__'
