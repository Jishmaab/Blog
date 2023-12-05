from rest_framework import permissions

from blog.models import User


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
                return request.user.user_type == User.UserChoices.Admin or request.user.is_staff



class IsPostOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        if not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user.is_staff
