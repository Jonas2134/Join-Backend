from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404

from board_app.models import Board
from column_app.models import Column
from task_app.models import Task


class IsBoardMemberOrOwner(BasePermission):
    message = "You are not allowed."

    def get_board(self, obj):
        if hasattr(obj, "members"):
            return obj
        if hasattr(obj, "board"):
            return obj.board
        if hasattr(obj, "column"):
            return obj.column.board
        return None

    def get_board_from_view(self, view):
        if "pk" in view.kwargs:
            return get_object_or_404(Board, pk=view.kwargs["pk"])
        if "column_pk" in view.kwargs:
            column = get_object_or_404(Column, pk=view.kwargs["column_pk"])
            return column.board
        if "task_pk" in view.kwargs:
            task = get_object_or_404(Task, pk=view.kwargs["task_pk"])
            return task.column.board
        return None

    def user_has_access(self, user, board):
        if board is None:
            return False
        return (
            user == board.owner
            or board.members.filter(id=user.id).exists()
        )

    def has_object_permission(self, request, view, obj):
        board = self.get_board(obj)
        return self.user_has_access(request.user, board)

    def has_permission(self, request, view):
        board = self.get_board_from_view(view)
        return self.user_has_access(request.user, board)
