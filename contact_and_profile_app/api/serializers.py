from rest_framework import serializers

from auth_app.models import CustomUserProfile as User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'tele_number', 'bio')
        read_only_fields = ('id', 'username', 'email')
