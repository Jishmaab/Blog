from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import authenticate, update_session_auth_hash
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
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

from permissions.permission import (IsAdminOrReadOnly, IsAdminUser,
                                    IsOwnerOrReadOnly)
from utils.exceptions import CustomException, fail, success

from .models import Category, Comment, Like, Post, Tag, User
from .serializers import (CategorySerializer, ChangePasswordSerializer,
                          CommentSerializer, DraftPostSerializer,
                          LikeSerializer, PostSerializer, TagSerializer,
                          UserSerializer)


class SignupView(APIView):
    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            try:
                validate_email(email)
            except ValidationError as email_error:
                raise CustomException(
                    {"status": "Invalid email format", "detail": email_error.detail})

            if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                raise CustomException(
                    {"status": "Username or email already in use"})
            user = serializer.create(serializer.validated_data)
            serializer = UserSerializer(user, context={'request': request})
            return Response(
                success(serializer.data),)
        raise CustomException(serializer.errors)


class LoginView(APIView):
    def post(self, request, format=None):
        try:
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

                response_data = {
                    "token": token.key,
                    "user": user_serializer.data,
                }
                return Response(success(response_data))

            raise AuthenticationFailed("Invalid username or password")

        except Exception as e:
            raise CustomException(str(e))


class LogoutView(APIView):
    permission_classes = [HasAPIKey, IsAuthenticated]

    def post(self, request: Request, format=None) -> Response:
        try:
            token = request.user.auth_token
            token.delete()
            return Response(
                success("Logged out successfully"))
        except Exception as e:
            raise CustomException(str(e))


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                update_session_auth_hash(request, user)
                return Response(success({'message': 'Password changed successfully.'}))
            return Response(fail({'error': 'Incorrect old password.'}))
        return Response(success())


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    pagination_class = PageNumberPagination
    # permission_classes = [IsAuthenticated, IsAdminUser, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return DraftPostSerializer
        return PostSerializer

    @action(detail=True, methods=['patch'])
    def publish(self, request, pk=None):
        post = self.get_object()
        post.status = Post.StatusChoices.Published
        post.save()
        return Response(success({'message': 'Post published successfully'}))

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, created_at=timezone.now())

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == Post.StatusChoices.Published:
            instance.status = Post.StatusChoices.Draft
            instance.save()
            return Response(success({'message': 'Post archived successfully'}))

        return super().delete(request, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class PostListView(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'content', 'tags']
    ordering_fields = ['created_at', 'category', 'author']
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated, HasAPIKey]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated, HasAPIKey]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticated, HasAPIKey]


class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


def handle_like(request, post_id):
     channel_layer = get_channel_layer()
     async_to_sync(channel_layer.group_send)(
        f"post_{post_id}",
        {
            'type': 'send_notification',
            'message': 'Someone liked your post!',
        }
    )


def index(request):
    return render(request, 'index.html')
