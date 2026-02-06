from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max
from django.shortcuts import get_object_or_404

from core.permissions import IsBoardMemberOrOwner, IsBoardActive
from column_app.models import Column
from task_app.models import Task
from .serializers import TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer


class TaskListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner, IsBoardActive]

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
    

class TaskDetailViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner, IsBoardActive]
    queryset = Task.objects.all()
    lookup_field = "pk"
    lookup_url_kwarg = "task_pk"

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return TaskUpdateSerializer
        return TaskSerializer
    
    def retrieve(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        task = self.get_object()
        task.delete()
        return Response({"detail": "Task deleted."}, status=status.HTTP_204_NO_CONTENT)
