from django.contrib.auth.forms import PasswordResetForm
from rest_framework import serializers

from utils.custompassword import PasswordField

from .models import *


class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.FileField()
    password = PasswordField(write_only=True, required=True)
    published_posts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name',
                  'user_type', 'profile_picture', 'bio', 'published_posts']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            profile_picture=validated_data.get('profile_picture'),
            bio=validated_data.get('bio')
        )
        user.set_password(validated_data.get('password'))
        user.save()
        return user

    def get_published_posts(self, user):
        posts = Post.objects.filter(
            author=user, status=Post.StatusChoices.Published)
        post_serializer = PostSerializer(posts, many=True)
        return post_serializer.data

    def to_representation(self, instance):
        is_signup = 'request' in self.context and 'signup' in self.context['request'].path_info
        if is_signup:
            self.fields.pop('published_posts')
        return super().to_representation(instance)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class ReplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Replay
        fields = '__all__'


class DraftPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'tags', 'category', 'status']


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'


class BioUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['bio']
