from datetime import datetime
from re import search

from django.contrib.auth.hashers import check_password
from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed
from django.http.request import HttpRequest
from rest_framework_api_key.models import APIKey

from blog.models import User


def get_identifier(key: str):
    pattern = r'(.+)\.'
    match = search(pattern, key)
    if match is None:
        return False
    return match.group(1)


def get_key(key: str):
    pattern = r'\.(.+)'
    match = search(pattern, key)
    if match is None:
        return False
    return key
    return match.group(1)


def validate_key(key: str):
    identifier = get_identifier(key)
    print(identifier)
    if identifier:
        keys = APIKey.objects.filter(
            prefix=identifier
        )
        # if any(map(lambda x: check_password()))
        if any(tuple(map(lambda x: check_password(get_key(key), x.key), keys))):
            return True
    return False


class HasAPIKey(permissions.BasePermission):
    def has_permission(self, request: HttpRequest, view):
        if 'HTTP_X_API_KEY' in request.META:
            key = request.META['HTTP_X_API_KEY']
            if validate_key(key):
                return True
            raise AuthenticationFailed('Invalid API Key')
        raise AuthenticationFailed('API Key not provided')


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
