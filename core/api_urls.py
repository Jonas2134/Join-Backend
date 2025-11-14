from django.urls import path, include

urlpatterns = [
    path('', include('auth_app.api.urls')),
    path('', include('boards_app.api.urls')),
]