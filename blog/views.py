from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.forms import ValidationError
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework import filters, generics, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from permissions.permission import IsAdminOrReadOnly, IsAdminUser
from root.viewsets import ModelViewSet
from utils.custompassword import PasswordValidator
from utils.exceptions import custom_exception_handler, fail, success

from .models import Category, Comment, Like, Post, Tag, User
from .pagination import DynamicPageSizePagination
from .serializers import (BioUpdateSerializer, CategorySerializer,
                          ChangePasswordSerializer, CommentSerializer,
                          DraftPostSerializer, LikeSerializer, LoginSerializer,
                          PostSerializer, TagSerializer, UserSerializer)


class SignupView(APIView):
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create(serializer.validated_data)
        serializer = UserSerializer(user, context={'request': request})
        return Response(success(serializer.data))


class LoginView(APIView):
    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            expiration_date = token.created + timedelta(days=1)
            if expiration_date <= timezone.now():
                token.delete()
                token = Token.objects.create(user=user)
            user_serializer = UserSerializer(user)
            data = {
                "token": token.key,
                "user": user_serializer.data,
            }
            return Response(success(data))
        raise AuthenticationFailed("Invalid password")


class LogoutView(APIView):
    permission_classes = [HasAPIKey, IsAuthenticated]

    def post(self, request: Request, format=None) -> Response:
        try:
            token = request.user.auth_token
            token.delete()
            return Response(
                success("Logged out successfully"))
        except Exception as e:
            raise custom_exception_handler(str(e))


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data.get('old_password')
            new_password = serializer.validated_data.get('new_password')
            if old_password == new_password:
                return Response(fail('New password must be different from the old password.'))
            try:
                PasswordValidator()(new_password)
            except ValidationError as e:
                return Response(fail(str(e)))
            try:
                validate_password(new_password, user=user)
            except DjangoValidationError as e:
                return Response(fail(e.messages))

            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                return Response(success('Password changed successfully.'))
            return Response(fail('Incorrect old password.'))
        return Response(fail(serializer.errors))


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostViewSet(ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return DraftPostSerializer
        return PostSerializer

    @action(detail=True, methods=['patch'])
    def publish(self, request, pk=None):
        post = self.get_object()

        if post.status == Post.StatusChoices.Published:

            return Response(fail("Already posted"))

        post.status = Post.StatusChoices.Published
        post.save()
        return Response(success('Post published successfully'))

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, created_at=timezone.now())

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == Post.StatusChoices.Published:
            instance.status = Post.StatusChoices.Draft
            instance.save()
            return Response(success('Post archived successfully'))

        return super().delete(request, *args, **kwargs)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class PostListView(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'content', 'tags__name']
    ordering_fields = ['created_at', 'category', 'author']
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated, HasAPIKey]


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated, IsAdminUser]

    def create(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            return Response(fail("You do not have permission to create categories."))
        return super().create(request, *args, **kwargs)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = DynamicPageSizePagination
    permission_classes = [IsAuthenticated]


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated, IsAdminUser]


class LikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')
        user_id = self.kwargs.get('user_id')

        if post_id:
            likes = Like.objects.filter(post_id=post_id)
        elif user_id:
            likes = Like.objects.filter(author_id=user_id)
        else:
            likes = Like.objects.all()

        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = LikeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(author=request.user)
                handle_like(request, serializer.instance.post.id)
                return Response(success("Like created successfully"))
            except IntegrityError as e:
                if 'unique constraint' in str(e).lower():
                    return Response(fail("Like already exists for this post."))
                else:
                    return Response(fail("Failed to create like."))
        return Response(fail("Failed to validate input"))



    def delete(self, request, *args, **kwargs):
        like_id = kwargs.get('pk')
        try:
            like = Like.objects.get(id=like_id, author=request.user)
            post_id = like.post.id
            like.delete()
            return Response(fail( "deleted"))
        except Like.DoesNotExist:
            return Response(fail())


def handle_like(request, post_id):
    channel_layer = get_channel_layer()
    message = 'Someone liked your post!'
    print(message)
    async_to_sync(channel_layer.group_send)(
        f"post_{post_id}",
        {
            'type': 'send_notification',
            'message': message,
        }
    )


def index(request):
    return render(request, 'index.html')


class UserProfileAPIView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(fail('User not found'))

        serializer = UserSerializer(user)
        return Response(serializer.data)


class BioUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        serializer = BioUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(success('Bio updated successfully'))
