from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class UserChoices(models.IntegerChoices):
        Admin = 0, 'Admin'
        User = 1, 'User'
    user_type = models.IntegerField(choices=UserChoices.choices, default=1)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', null=True, blank=True)
    bio = models.CharField(max_length=35, null=True, blank=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'user'


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'tag'


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'category'


class Post(models.Model):
    class StatusChoices(models.IntegerChoices):
        Draft = 0, 'Draft'
        Published = 1, 'Published'
    title = models.CharField(max_length=35, null=True, blank=True)
    content = models.CharField(max_length=35, null=True, blank=True)
    image = models.ImageField(
        upload_to='images/', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=StatusChoices.choices, default=1)

    class Meta:
        db_table = 'post'


class Comment(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    class Meta:
        db_table = 'comment'


class Replay(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    class Meta:
        db_table = 'replay'


class Like(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    class Meta:
        db_table = 'like'


class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'notification'
