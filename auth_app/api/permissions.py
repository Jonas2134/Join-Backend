from rest_framework.permissions import BasePermission


class NotGuest(BasePermission):
    message = "Guests cannot perform this action."

    def has_permission(self, request, view):
        return not (request.user.is_authenticated and request.user.is_guest)
