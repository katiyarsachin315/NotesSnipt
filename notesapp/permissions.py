from rest_framework.permissions import BasePermission


def is_admin(user):
    return user.is_authenticated and user.is_admin


def is_owner(user, obj):
    return obj.user == user

class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_admin(request.user) or is_owner(request.user, obj)

class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user and (
            request.user.is_admin or request.user.is_superuser
        )