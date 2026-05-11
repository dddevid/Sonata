from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, ServerSettings


class UserSerializer(serializers.ModelSerializer):
    isAdmin = serializers.BooleanField(source='is_admin_user', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'isAdmin',
            'max_bit_rate', 'avatar', 'scrobbling_enabled',
            'stream_role', 'download_role', 'upload_role',
            'playlist_role', 'share_role', 'date_joined',
        )
        read_only_fields = ('id', 'date_joined', 'isAdmin')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)

        # Ensure encryption key exists before setting subsonic password
        from django.conf import settings
        if not settings.SUBSONIC_ENCRYPTION_KEY:
            from apps.accounts.models import ServerSettings
            settings_obj = ServerSettings.get()
            if not settings_obj.subsonic_encryption_key:
                settings_obj.generate_subsonic_encryption_key()
                settings_obj.save(update_fields=['subsonic_encryption_key'])
            # Update running settings
            settings.SUBSONIC_ENCRYPTION_KEY = settings_obj.subsonic_encryption_key

        user.set_subsonic_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Incorrect current password.')
        return value


class ServerSettingsSerializer(serializers.ModelSerializer):
    """Serializer for server settings - admin only."""

    # Mask sensitive fields in output
    ldap_bind_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    secret_key = serializers.CharField(read_only=True)
    subsonic_encryption_key = serializers.CharField(read_only=True)

    class Meta:
        model = ServerSettings
        fields = [
            'id',
            # Core
            'secret_key',
            'debug',
            'server_name',
            # Registration
            'allow_self_register',
            # CORS
            'cors_allowed_origins',
            # JWT
            'access_token_lifetime_minutes',
            'refresh_token_lifetime_days',
            # Rate limiting
            'throttle_user_rate',
            'throttle_anon_rate',
            # LDAP
            'ldap_enabled',
            'ldap_server_uri',
            'ldap_bind_dn',
            'ldap_bind_password',
            'ldap_user_search_base',
            'ldap_user_search_filter',
            'ldap_attr_username',
            'ldap_attr_email',
            'ldap_attr_first_name',
            'ldap_attr_last_name',
            'ldap_auto_create_users',
            'ldap_default_role',
            # Security
            'subsonic_encryption_key',
        ]
        read_only_fields = ['id', 'secret_key', 'subsonic_encryption_key']
