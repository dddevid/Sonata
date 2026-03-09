from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import logging


class User(AbstractUser):
    """
    Extended user model.
    - First user created automatically becomes admin.
    - subsonic_password is stored encrypted when SUBSONIC_ENCRYPTION_KEY is set.
    """
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    # Plain-text password used for Subsonic token auth (separate from Django auth)
    subsonic_password = models.CharField(max_length=255, blank=True)
    max_bit_rate = models.IntegerField(default=0)  # 0 = unlimited
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    email = models.EmailField(blank=True)
    scrobbling_enabled = models.BooleanField(default=True)
    download_role = models.BooleanField(default=True)
    upload_role = models.BooleanField(default=False)
    playlist_role = models.BooleanField(default=True)
    cover_art_role = models.BooleanField(default=False)
    comment_role = models.BooleanField(default=False)
    podcast_role = models.BooleanField(default=False)
    stream_role = models.BooleanField(default=True)
    jukebox_role = models.BooleanField(default=False)
    share_role = models.BooleanField(default=False)
    video_conversion_role = models.BooleanField(default=False)

    class Meta:
        db_table = 'accounts_user'

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def _get_fernet(self):
        key = getattr(settings, 'SUBSONIC_ENCRYPTION_KEY', None)
        if not key:
            # Fallback for dev if not set (not recommended for production)
            return None
        try:
            return Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            logging.error(f"Fernet initialization failed: {e}")
            return None

    def get_subsonic_password(self):
        """Decrypts and returns the subsonic password."""
        if not self.subsonic_password:
            return ""
        
        # If it doesn't look like Fernet (e.g. legacy plain text), return as is
        # Fernet tokens start with 'gAAAA'
        if not self.subsonic_password.startswith('gAAAA'):
            return self.subsonic_password

        f = self._get_fernet()
        if not f:
            return self.subsonic_password
            
        try:
            return f.decrypt(self.subsonic_password.encode()).decode()
        except Exception as e:
            logging.error(f"Failed to decrypt subsonic password for {self.username}: {e}")
            return self.subsonic_password

    def set_subsonic_password(self, raw_password):
        """Encrypts and sets the subsonic password."""
        if not raw_password:
            self.subsonic_password = ""
            return

        f = self._get_fernet()
        if not f:
            # Insecure configuration: refuse to silently store plain-text
            raise ValueError("SUBSONIC_ENCRYPTION_KEY is not configured; cannot set subsonic password securely.")

        try:
            self.subsonic_password = f.encrypt(raw_password.encode()).decode()
        except Exception as e:
            logging.error(f"Failed to encrypt subsonic password for {self.username}: {e}")
            self.subsonic_password = raw_password

    def save(self, *args, **kwargs):
        # First user ever becomes admin
        if not self.pk and User.objects.count() == 0:
            self.role = self.Role.ADMIN
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class ServerSettings(models.Model):
    """
    Singleton-style settings for the Sonata server.
    Currently controls whether self-registration is allowed.
    """

    allow_self_register = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Server settings"
        verbose_name_plural = "Server settings"

    def __str__(self):
        return "Server settings"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
