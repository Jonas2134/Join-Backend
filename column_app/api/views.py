from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.permissions import IsBoardMemberOrOwner, IsBoardActive
from board_app.models import Board
from column_app.models import Column
from .serializers import ColumnSerializer, ColumnCreateSerializer, ColumnUpdateSerializer


class ColumnListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner, IsBoardActive]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ColumnCreateSerializer
        return ColumnSerializer

    def get_board(self):
        board_pk = self.kwargs['board_pk']
        return get_object_or_404(Board, pk=board_pk)

    def get_queryset(self):
        board = self.get_board()
        return board.columns.prefetch_related('tasks').order_by('position')

    def create(self, request, *args, **kwargs):
        board = self.get_board()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(board=board)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ColumnDetailViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsBoardMemberOrOwner, IsBoardActive]
    queryset = Column.objects.all()
    lookup_field = "pk"
    lookup_url_kwarg = "column_pk"

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return ColumnUpdateSerializer
        return ColumnSerializer

    def retrieve(self, request, *args, **kwargs):
        column = self.get_object()
        serializer = self.get_serializer(column)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        column = self.get_object()
        serializer = self.get_serializer(column, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        column = self.get_object()
        column.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
