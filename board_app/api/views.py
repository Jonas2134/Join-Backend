from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from board_app.models import Board
from .serializers import BoardListSerializer, BoardCreateSerializer, BoardDetailSerializer, BoardUpdateSerializer


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
