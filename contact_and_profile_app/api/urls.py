from django.urls import path

from .views import ProfileView, UserListView, AddContactView, ContactListView, RemoveContactView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/add-contact/', AddContactView.as_view(), name='add-contact'),
    path('contacts/', ContactListView.as_view(), name='contact-list'),
    path('contacts/<int:user_id>/', RemoveContactView.as_view(), name='remove-contact'),
]

