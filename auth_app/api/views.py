from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

class RegisterView(generics.CreateAPIView):
  pass

# class LoginView(TokenObtainPairView):
#   pass

# class LogoutView(APIView):
#   pass

# class CookieTokenRefreshView(TokenRefreshView):
#   pass
