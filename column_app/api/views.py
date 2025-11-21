from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max
from django.shortcuts import get_object_or_404

from core.permissions import IsBoardMemberOrOwner
from board_app.models import Board
from column_app.models import Column
from .serializers import ColumnSerializer, ColumnCreateSerializer, ColumnUpdateSerializer


class ColumnListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ColumnCreateSerializer
        return ColumnSerializer

    def get_board(self):
        pk = self.kwargs['pk']
        return get_object_or_404(Board, pk=pk)

    def get_queryset(self):
        board = self.get_board()
        return board.columns.order_by('position')

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        board = self.get_board()
        max_position = board.columns.aggregate(Max('position'))['position__max'] or 0
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(board=board, position=max_position + 1)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ColumnDetailViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner]

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return ColumnUpdateSerializer
        return ColumnSerializer

    def get_column(self):
        pk = self.kwargs.get('column_pk')
        return get_object_or_404(Column, pk=pk)

    def get_object(self):
        return self.get_column()

    def retrieve(self, request, *args, **kwargs):
        column = self.get_object()
        self.check_permissions(request)
        serializer = self.get_serializer(column)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        column = self.get_object()
        self.check_permissions(request)
        serializer = self.get_serializer(column, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        column = self.get_object()
        self.check_permissions(request)
        column.delete()
        return Response({"detail": "Column deleted."}, status=status.HTTP_204_NO_CONTENT)
