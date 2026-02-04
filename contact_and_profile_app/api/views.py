from django.shortcuts import get_object_or_404
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .serializers import ProfileSerializer, UserListSerializer, ContactSerializer
from auth_app.models import CustomUserProfile as User


class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        queryset = self.get_queryset()
        user = self.request.user
        profile = get_object_or_404(queryset, id=user.id)
        return profile

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class UserListView(generics.ListAPIView):
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        contact_ids = user.contacts.values_list('id', flat=True)

        queryset = User.objects.exclude(
            id__in=contact_ids
        ).exclude(
            id=user.id
        ).exclude(
            is_guest=True
        )

        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(username__icontains=search)

        return queryset


class AddContactView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if request.user.is_guest:
            return Response(
                {"detail": "Guest users cannot add contacts."},
                status=status.HTTP_403_FORBIDDEN
            )

        user_to_add = get_object_or_404(User, id=user_id)

        if user_to_add.is_guest:
            return Response(
                {"detail": "Cannot add a guest user as contact."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user_to_add == request.user:
            return Response(
                {"detail": "You cannot add yourself as a contact."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.contacts.filter(id=user_id).exists():
            return Response(
                {"detail": "User is already in your contacts."},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.contacts.add(user_to_add)
        return Response(
            {"detail": "Contact added successfully."},
            status=status.HTTP_201_CREATED
        )


class ContactListView(generics.ListAPIView):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.contacts.all()


class RemoveContactView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        user_to_remove = get_object_or_404(User, id=user_id)

        if not request.user.contacts.filter(id=user_id).exists():
            return Response(
                {"detail": "User is not in your contacts."},
                status=status.HTTP_404_NOT_FOUND
            )

        request.user.contacts.remove(user_to_remove)
        return Response(status=status.HTTP_204_NO_CONTENT)
