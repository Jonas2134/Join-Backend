from rest_framework import status, generics, viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Max
from django.shortcuts import get_object_or_404

from boards_app.models import Board, Column
from .serializers import BoardListSerializer, BoardCreateSerializer, BoardDetailSerializer, BoardUpdateSerializer, ColumnCreateSerializer, ColumnUpdateSerializer


class BoardListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Board.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BoardCreateSerializer
        return BoardListSerializer
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BoardDetailViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Board.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BoardDetailSerializer
        if self.action == 'partial_update':
            return BoardUpdateSerializer
        return BoardDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        board = self.get_object()
        if request.user != board.owner and request.user not in board.members.all():
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(board)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, *args, **kwargs):
        board = self.get_object()
        if request.user != board.owner and request.user not in board.members.all():
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(board, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(BoardDetailSerializer(updated).data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        board = self.get_object()
        if request.user != board.owner:
            return Response({"detail": "Only the owner can delete the board."}, status=status.HTTP_403_FORBIDDEN)
        board.delete()
        return Response({"detail": "Board deleted."}, status=status.HTTP_204_NO_CONTENT)


class ColumnCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ColumnCreateSerializer

    def get_board(self, pk):
        return get_object_or_404(Board, pk=pk)

    def create(self, request, *args, **kwargs):
        board_pk = self.kwargs.get('pk')
        board = self.get_board(board_pk)
        max_position = board.columns.aggregate(Max('position'))['position__max'] or 0
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(board=board, position=max_position + 1)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ColumnUpdateDestroyView(mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ColumnUpdateSerializer

    def get_board(self, pk):
        return get_object_or_404(Board, pk=pk)

    def get_column(self, board, column_pk):
        return get_object_or_404(Column, board=board, pk=column_pk)

    def get_object(self):
        board_pk = self.kwargs.get('pk')
        column_pk = self.kwargs.get('column_pk')
        board = self.get_board(board_pk)
        return self.get_column(board, column_pk)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)