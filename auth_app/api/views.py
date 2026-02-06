import uuid
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .serializers import RegisterSerializer, LoginSerializer, PasswordChangeSerializer
from auth_app.models import CustomUserProfile


COOKIE_KWARGS = {
    'httponly': True,
    'secure': False,
    'samesite': 'Lax'
}

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            message = {"detail": "User created successfully!"}
            return Response(message, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            data = response.data
            refresh = data.get('refresh')
            access = data.get('access')
            response = Response({"detail": "Login successfully!"}, status=status.HTTP_200_OK)
            response.set_cookie(key='refresh_token', value=refresh, **COOKIE_KWARGS)
            response.set_cookie(key='access_token', value=access, **COOKIE_KWARGS)
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Token invalid"}, status=status.HTTP_400_BAD_REQUEST)

        response = Response({"detail": "Log-Out successfully!"}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')

        if user.is_guest:
            user.delete()

        return response


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        access_token = serializer.validated_data.get("access")
        new_refresh = serializer.validated_data.get("refresh")
        response = Response({"access": "Access Token refreshed successfully."}, status=status.HTTP_200_OK)
        response.set_cookie(key='access_token', value=access_token, **COOKIE_KWARGS)
        if new_refresh:
            response.set_cookie(key='refresh_token', value=new_refresh, **COOKIE_KWARGS)
        return response


class GuestLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        guest_user = CustomUserProfile.objects.create(
            username=f"guest_{uuid.uuid4().hex[:8]}",
            is_guest=True
        )
        guest_user.set_unusable_password()
        guest_user.save()

        refresh = RefreshToken.for_user(guest_user)
        access = refresh.access_token

        response = Response({
            "detail": "Guest Login successfully!",
            "user": {
                "id": guest_user.id,
                "username": guest_user.username,
                "is_guest": guest_user.is_guest
            }
        }, status=status.HTTP_200_OK)

        response.set_cookie(key='refresh_token', value=str(refresh), **COOKIE_KWARGS)
        response.set_cookie(key='access_token', value=str(access), **COOKIE_KWARGS)

        return response


class AuthStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "is_authenticated": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_guest": user.is_guest,
            }
        }, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
