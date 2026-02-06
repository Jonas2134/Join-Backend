from django.urls import path

from .views import (
    RegisterView, LoginView, LogoutView, CookieTokenRefreshView,
    GuestLoginView, AuthStatusView, PasswordChangeView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('guest-login/', GuestLoginView.as_view(), name='guest_login'),
    path('auth/status/', AuthStatusView.as_view(), name='auth_status'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
]
