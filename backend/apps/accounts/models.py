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
        # First try settings, then fallback to database
        key = getattr(settings, 'SUBSONIC_ENCRYPTION_KEY', None)
        if not key:
            # Fallback to database directly (needed at startup before settings loaded)
            try:
                settings_obj = ServerSettings.get()
                key = settings_obj.subsonic_encryption_key
            except Exception:
                pass
        if not key:
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
            # Auto-generate key if missing
            try:
                settings_obj = ServerSettings.get()
                if not settings_obj.subsonic_encryption_key:
                    settings_obj.generate_subsonic_encryption_key()
                    settings_obj.save(update_fields=['subsonic_encryption_key'])
                # Update settings and retry
                from django.conf import settings
                settings.SUBSONIC_ENCRYPTION_KEY = settings_obj.subsonic_encryption_key
                f = self._get_fernet()
            except Exception as e:
                logging.error(f"Failed to generate encryption key: {e}")
                raise ValueError("SUBSONIC_ENCRYPTION_KEY is not configured; cannot set subsonic password securely.")

        if not f:
            raise ValueError("SUBSONIC_ENCRYPTION_KEY is not configured; cannot set subsonic password securely.")

        try:
            self.subsonic_password = f.encrypt(raw_password.encode()).decode()
        except Exception as e:
            logging.error(f"Failed to encrypt subsonic password for {self.username}: {e}")
            raise

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
    All configuration stored in database - editable by admin via API.
    """

    # Core settings
    secret_key = models.CharField(max_length=100, blank=True, help_text="Auto-generated Django SECRET_KEY")
    debug = models.BooleanField(default=False, help_text="Debug mode (never enable in production)")
    server_name = models.CharField(max_length=100, default='Sonata')

    # Registration settings
    allow_self_register = models.BooleanField(default=True)

    # CORS settings
    cors_allowed_origins = models.TextField(
        blank=True,
        default='http://localhost:5173\nhttp://localhost:3000',
        help_text="One origin per line"
    )

    # JWT settings
    access_token_lifetime_minutes = models.IntegerField(default=1440, help_text="Default: 1440 (1 day)")
    refresh_token_lifetime_days = models.IntegerField(default=7, help_text="Default: 7 days")

    # Rate limiting
    throttle_user_rate = models.CharField(max_length=20, default='1000/day')
    throttle_anon_rate = models.CharField(max_length=20, default='100/day')

    # LDAP settings (optional)
    ldap_enabled = models.BooleanField(default=False)
    ldap_server_uri = models.CharField(max_length=255, blank=True, default='ldap://localhost')
    ldap_bind_dn = models.CharField(max_length=255, blank=True)
    ldap_bind_password = models.CharField(max_length=255, blank=True)
    ldap_user_search_base = models.CharField(max_length=255, blank=True, default='ou=users,dc=example,dc=com')
    ldap_user_search_filter = models.CharField(max_length=255, blank=True, default='(uid=%(user)s)')
    ldap_attr_username = models.CharField(max_length=50, blank=True, default='uid')
    ldap_attr_email = models.CharField(max_length=50, blank=True, default='mail')
    ldap_attr_first_name = models.CharField(max_length=50, blank=True, default='givenName')
    ldap_attr_last_name = models.CharField(max_length=50, blank=True, default='sn')
    ldap_auto_create_users = models.BooleanField(default=True)
    ldap_default_role = models.CharField(max_length=10, choices=User.Role.choices, default=User.Role.USER)

    # Security
    subsonic_encryption_key = models.CharField(max_length=100, blank=True, help_text="Key for encrypting Subsonic passwords")

    class Meta:
        verbose_name = "Server settings"
        verbose_name_plural = "Server settings"

    def __str__(self):
        return "Server settings"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def get_cors_origins_list(self):
        """Return CORS origins as a list."""
        if not self.cors_allowed_origins:
            return []
        return [origin.strip() for origin in self.cors_allowed_origins.split('\n') if origin.strip()]

    def generate_secret_key(self):
        """Generate a new random SECRET_KEY."""
        import secrets
        self.secret_key = secrets.token_urlsafe(50)
        return self.secret_key

    def generate_subsonic_encryption_key(self):
        """Generate a Fernet-compatible encryption key."""
        from cryptography.fernet import Fernet
        self.subsonic_encryption_key = Fernet.generate_key().decode()
        return self.subsonic_encryption_key
