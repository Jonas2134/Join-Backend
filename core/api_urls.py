from django.urls import path, include

urlpatterns = [
    path('', include('auth_app.api.urls')),
    path('', include('board_app.api.urls')),
    path('', include('column_app.api.urls')),
    path('', include('task_app.api.urls')),
    path('', include('contact_and_profile_app.api.urls')),
]