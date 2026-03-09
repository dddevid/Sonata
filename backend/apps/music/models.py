from django.db import models
from django.utils import timezone
from apps.accounts.models import User


class MusicFolder(models.Model):
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=4096, unique=True)
    enabled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)
    song_count = models.IntegerField(default=0)
    album_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=512)
    album_count = models.IntegerField(default=0)
    mb_id = models.CharField(max_length=36, blank=True)  # MusicBrainz
    biography = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    image_path = models.CharField(max_length=4096, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Album(models.Model):
    name = models.CharField(max_length=512)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='albums')
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    cover_art_path = models.CharField(max_length=4096, blank=True)
    duration = models.IntegerField(default=0)  # seconds
    song_count = models.IntegerField(default=0)
    mb_id = models.CharField(max_length=36, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'artist')

    def __str__(self):
        return f'{self.artist.name} – {self.name}'

    def cover_art_id(self):
        return f'al-{self.pk}'


class Song(models.Model):
    title = models.CharField(max_length=512)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='songs')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='songs')
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    music_folder = models.ForeignKey(MusicFolder, on_delete=models.CASCADE)
    track = models.IntegerField(null=True, blank=True)
    disc_number = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(default=0)       # seconds
    bit_rate = models.IntegerField(default=0)       # kbps
    size = models.BigIntegerField(default=0)        # bytes
    suffix = models.CharField(max_length=10, blank=True)   # mp3, flac …
    content_type = models.CharField(max_length=100, blank=True)
    path = models.CharField(max_length=4096, unique=True)
    mb_id = models.CharField(max_length=36, blank=True)
    play_count = models.BigIntegerField(default=0)
    last_played = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['disc_number', 'track', 'title']

    def __str__(self):
        return self.title

    def cover_art_id(self):
        return f'mf-{self.pk}'


class Starred(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, null=True, blank=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, null=True, blank=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, null=True, blank=True)
    starred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [
            ('user', 'song'),
            ('user', 'album'),
            ('user', 'artist'),
        ]


class UserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, null=True, blank=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, null=True, blank=True)
    rating = models.IntegerField()  # 1–5

    class Meta:
        unique_together = [('user', 'song'), ('user', 'album')]


class Playlist(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    comment = models.TextField(blank=True)
    public = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    changed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='entries')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']
        unique_together = ('playlist', 'position')


class InternetRadioStation(models.Model):
    name = models.CharField(max_length=255)
    stream_url = models.URLField()
    home_page_url = models.URLField(blank=True)
    created = models.DateTimeField(auto_now_add=True)


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.BigIntegerField(default=0)  # milliseconds
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    changed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'song')


class PlayQueue(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='play_queue')
    songs = models.ManyToManyField(Song, through='PlayQueueEntry', blank=True)
    current = models.ForeignKey(
        Song, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    position = models.BigIntegerField(default=0)  # ms
    changed = models.DateTimeField(auto_now=True)
    changed_by = models.CharField(max_length=255, blank=True)


class PlayQueueEntry(models.Model):
    queue = models.ForeignKey(PlayQueue, on_delete=models.CASCADE, related_name='entries')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    position = models.IntegerField()

    class Meta:
        ordering = ['position']


class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    url_token = models.CharField(max_length=64, unique=True)
    expires = models.DateTimeField(null=True, blank=True)
    last_visited = models.DateTimeField(null=True, blank=True)
    visit_count = models.IntegerField(default=0)
    songs = models.ManyToManyField(Song, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    changed = models.DateTimeField(auto_now=True)


class ScanStatus(models.Model):
    """Singleton tracking current scan state."""
    is_scanning = models.BooleanField(default=False)
    count = models.IntegerField(default=0)
    folder_count = models.IntegerField(default=0)
    last_scan = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Scan Status'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ActiveStream(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    client = models.CharField(max_length=255, blank=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_seen']
        unique_together = ('user', 'client')

    def __str__(self):
        return f"{self.user.username} playing {self.song.title} on {self.client}"

