from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max
from django.shortcuts import get_object_or_404

from column_app.models import Column
from tasks_app.models import Task
from .serializers import TaskSerializer, TaskCreateSerializer


class TaskListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TaskCreateSerializer
        return TaskSerializer
    
    def get_column(self):
        pk = self.kwargs['column_pk']
        return get_object_or_404(Column, pk=pk)
    
    def get_queryset(self):
        column = self.get_column()
        return column.tasks.order_by('position')
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        column = self.get_column()
        max_position = column.tasks.aggregate(Max('position'))['position__max'] or 0
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(column=column, position=max_position + 1)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
