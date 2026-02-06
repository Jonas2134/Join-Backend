from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404

from board_app.models import Board
from column_app.models import Column
from task_app.models import Task


class IsBoardOwner(BasePermission):
    message = "Only the board owner is allowed to perform this action."

    def get_board(self, obj):
        if hasattr(obj, "owner"):
            return obj
        if hasattr(obj, "board"):
            return obj.board
        if hasattr(obj, "column"):
            return obj.column.board
        return None

    def get_board_from_view(self, view):
        if "pk" in view.kwargs:
            return get_object_or_404(Board, pk=view.kwargs["pk"])
        if "board_pk" in view.kwargs:
            return get_object_or_404(Board, pk=view.kwargs["board_pk"])
        return None

    def has_object_permission(self, request, view, obj):
        board = self.get_board(obj)
        return board is not None and request.user == board.owner

    def has_permission(self, request, view):
        board = self.get_board_from_view(view)
        if board is None:
            return True
        return request.user == board.owner


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


class IsBoardActive(BasePermission):
    message = "This board is archived. No modifications allowed."

    def _get_board(self, view):
        if "pk" in view.kwargs:
            return get_object_or_404(Board, pk=view.kwargs["pk"])
        if "column_pk" in view.kwargs:
            column = get_object_or_404(Column, pk=view.kwargs["column_pk"])
            return column.board
        if "task_pk" in view.kwargs:
            task = get_object_or_404(Task, pk=view.kwargs["task_pk"])
            return task.column.board
        return None

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        board = self._get_board(view)
        if board is None:
            return True
        return board.is_active
