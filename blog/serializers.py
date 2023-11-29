from django.contrib.auth.forms import PasswordResetForm
from rest_framework import serializers

from utils.custompassword import PasswordField

from .models import *


class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.FileField()
    password = PasswordField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name',
                  'last_name', 'user_type', 'profile_picture', 'bio']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            user_type=validated_data.get('user_type'),
            profile_picture=validated_data.get('profile_picture'),
            bio=validated_data.get('bio')
        )
        user.set_password(validated_data.get('password'))
        user.save()
        return user


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