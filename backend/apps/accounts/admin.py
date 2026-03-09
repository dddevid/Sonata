from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ServerSettings


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')

    @admin.display(description='Subsonic Password (decrypted)')
    def decrypted_subsonic_password(self, obj):
        return obj.get_subsonic_password()

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Sonata', {'fields': ('role', 'decrypted_subsonic_password', 'max_bit_rate', 'avatar')}),
        ('Roles', {'fields': (
            'stream_role', 'download_role', 'upload_role', 'playlist_role',
            'cover_art_role', 'comment_role', 'podcast_role', 'jukebox_role',
            'share_role', 'video_conversion_role', 'scrobbling_enabled',
        )}),
    )
    readonly_fields = ('decrypted_subsonic_password',)


@admin.register(ServerSettings)
class ServerSettingsAdmin(admin.ModelAdmin):
    list_display = ('allow_self_register',)

    def has_add_permission(self, request):
        # Enforce singleton: only one settings row.
        if ServerSettings.objects.exists():
            return False
        return super().has_add_permission(request)
