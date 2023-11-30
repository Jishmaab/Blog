from django.urls import path
from rest_framework.routers import DefaultRouter

from blog import views

router = DefaultRouter()
router.register(r'posts', views.PostViewSet, basename='post'),
router.register(r'comment', views.CommentViewSet, basename='comment'),
router.register(r'user', views.UserViewSet, basename='user'),
router.register(r'category', views.CategoryViewSet, basename='category'),
router.register(r'tag', views.TagViewSet, basename='tag'),
router.register(r'likes', views.LikeViewSet, basename='like')

urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('change-password/', views.ChangePasswordAPIView.as_view(),
         name='change-password'),
    path('postlist/', views.PostListView.as_view(), name='post-list'),

] + router.urls
