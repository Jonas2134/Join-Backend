from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from auth_app.models import CustomUserProfile as User


class RegisterSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'repeated_password')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'password': {'write_only': True},
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already taken.")
        return value

    def validate_repeated_password(self, value):
        pw = self.initial_data.get('password')
        if value != pw:
            raise serializers.ValidationError("Passwords do not match.")
        return value
        

    def save(self, **kwargs):
        pw = self.validated_data['password']
        email = self.validated_data['email']
        username = self.validated_data['username']
        user = User(email=email, username=username, is_active=True, is_guest=False)
        user.set_password(pw)
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = self._check_user_exist(username)
        self._check_password(user, password)

        attrs['username'] = user.username
        data = super().validate(attrs)
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
        }
        return data

    def _check_user_exist(self, username):
        try:
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this username does not exist.")
    
    def _check_password(self, user, password) -> None:
        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password.")
