from rest_framework.permissions import BasePermission

from boards_app.models import Board

class IsBoardMemberOrOwner(BasePermission):
    message = "You do not have permission to access this board."

    def has_object_permission(self, request, view, obj):
        board = getattr(obj, 'board', None)
        if board is None and hasattr(obj, 'column'):
            board = obj.column.board
        if board is None:
            return False
        user = request.user
        if board.owner_id == user.id:
            return True
        if board.members.filter(id=user.id).exists():
            return True
        return False
    
    def has_permission(self, request, view):
        board_pk = view.kwargs.get('pk')
        if not board_pk:
            return False
        try:
            board = Board.objects.get(pk=board_pk)
        except Board.DoesNotExist:
            return False
        user = request.user
        if board.owner_id == user.id:
            return True
        if board.members.filter(id=user.id).exists():
            return True
        return False
