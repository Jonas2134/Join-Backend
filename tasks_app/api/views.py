from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class TaskListCreateView(generics.ListCreateAPIView):
    pass
