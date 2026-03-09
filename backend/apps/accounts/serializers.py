from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


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
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.set_subsonic_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=4)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Incorrect current password.')
        return value
