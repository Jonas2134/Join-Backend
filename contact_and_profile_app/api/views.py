from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class ProfileView(generics.RetrieveUpdateAPIView):
    pass
