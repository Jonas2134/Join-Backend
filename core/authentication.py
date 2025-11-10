from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
  """
  Custom JWT authentication that reads the token from an 'access_token' HttpOnly cookie.
  """
  def authenticate(self, request):
    access_token = request.COOKIES.get("access_token")
    if not access_token:
      return super().authenticate(request)
    try:
      validated_token = self.get_validated_token(access_token)
      return self.get_user(validated_token), validated_token
    except InvalidToken:
      return None
