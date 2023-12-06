
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import (APIRequestFactory, APITestCase)
from blog.management.commands import api_key_gen

from blog.models import Category, Comment, Post, Tag, User
from root.settings import API_KEY_CUSTOM_HEADER


class SignupViewTestCase(APITestCase):
    def setUp(self):
        self.test_user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password@123',
            first_name='firstname',
            last_name='lastname',
            user_type=1,
            profile_picture='',
            bio='bio'
        )

    def test_signup_successful(self):
        url = reverse('signup')
        data = {
            'username': 'dom',
            'email': 'dom00@example.com',
            'password': 'Password@123',
            'first_name': 'dom',
            'last_name': 'george',
            'user_type': 1,
            'profile_picture': self.generate_image_file(),
            'bio': 'bio'
        }

        response = self.client.post(
            url, data, format='multipart', **{'x-api-key': 'eNR3fmpc.NwaQnP8j1vTB1lCpzNtIru4lPn0FhF2I'}
        )
        print(response.request)
        print(response.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], True)

    def generate_image_file(self):
        content = get_random_string(1024)
        return SimpleUploadedFile("test_image.jpg", content.encode(), content_type="image/jpeg")


class LoginViewTests(APIRequestFactory):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.login_url = reverse('/api/login')

    def test_login_successful(self):
        data = {
            'username': 'testuser',
            'password': 'testpassword',
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        data = {
            'username': 'testuser',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('non_field_errors', response.data)

    def test_login_missing_credentials(self):
        data = {}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('password', response.data)


class LogoutViewTestCase(APIRequestFactory):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.api_key = f'Token {self.token.key}'

    def test_logout_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.api_key)
        response = self.client.post('/api/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Token.objects.filter(user=self.user).exists())

        self.assertEqual(response.data, {'message': 'Logged out successfully'})

    def test_logout_view_without_authentication(self):
        response = self.client.post('/api/logout/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data, {'detail': 'Authentication credentials were not provided.'})


class ChangePasswordAPITestCase(APIRequestFactory):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.url = '/change-password/'

    def test_change_password_success(self):
        data = {
            'old_password': 'testpassword',
            'new_password': 'newtestpassword',
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data, {'message': 'Password changed successfully.'})

    def test_change_password_incorrect_old_password(self):
        data = {
            'old_password': 'incorrectpassword',
            'new_password': 'newtestpassword',
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Incorrect old password.', response.data['error'])

    def test_change_password_unauthenticated_user(self):
        data = {
            'old_password': 'testpassword',
            'new_password': 'newtestpassword',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            'Authentication credentials were not provided.', response.data['detail'])


class CommentViewSetTestCase(APIRequestFactory):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.comment_data = {
            'content': 'Test comment content',
        }
        self.url = reverse('/api/comment/')

    def test_create_comment_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, data=self.comment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(
            content='Test comment content').exists())

    def test_create_comment_unauthenticated_user(self):
        response = self.client.post(self.url, data=self.comment_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Comment.objects.filter(
            content='Test comment content').exists())

    def test_pagination(self):
        for i in range(15):
            Comment.objects.create(content=f'Comment {i}', author=self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_permission(self):
        restricted_user = get_user_model().objects.create_user(
            username='restricteduser',
            password='testpassword'
        )
        self.client.force_authenticate(user=restricted_user)

        response = self.client.post(self.url, data=self.comment_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PostViewSetTestCase(APIRequestFactory):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.admin_user = get_user_model().objects.create_user(
            username='adminuser',
            password='adminpassword',
            is_staff=True
        )
        self.draft_post_data = {
            'title': 'Test Draft Post',
            'content': 'Test content',
            'author': self.user.id,
            'status': Post.StatusChoices.Draft,
        }
        self.published_post_data = {
            'title': 'Test Published Post',
            'content': 'Test content',
            'author': self.user.id,
            'status': Post.StatusChoices.Published,
        }
        self.url = reverse('post')

    def test_create_draft_post_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, data=self.draft_post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], Post.StatusChoices.Draft)

    def test_create_published_post_admin_user(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.url, data=self.published_post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], Post.StatusChoices.Published)

    def test_pagination(self):
        for i in range(15):
            Post.objects.create(
                title=f'Test Post {i}',
                content=f'Test content {i}',
                author=self.user,
                status=Post.StatusChoices.Published
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_publish_post(self):
        draft_post = Post.objects.create(
            title='Test Draft Post',
            content='Test content',
            author=self.user,
            status=Post.StatusChoices.Draft
        )

        publish_url = reverse('post-publish', kwargs={'pk': draft_post.id})
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(publish_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'],
                         'Post published successfully')
        draft_post.refresh_from_db()
        self.assertEqual(draft_post.status, Post.StatusChoices.Published)

    def test_archive_published_post(self):
        published_post = Post.objects.create(
            title='Test Published Post',
            content='Test content',
            author=self.user,
            status=Post.StatusChoices.Published
        )

        archive_url = reverse('post-detail', kwargs={'pk': published_post.id})
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(archive_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'],
                         'Post archived successfully')
        published_post.refresh_from_db()
        self.assertEqual(published_post.status, Post.StatusChoices.Draft)


class UserViewSetTestCase(APIRequestFactory):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.admin_user = get_user_model().objects.create_user(
            username='adminuser',
            password='adminpassword',
            is_staff=True
        )
        self.url = reverse('user-list')

    def test_list_users_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_users_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_pagination(self):
        for i in range(15):
            get_user_model().objects.create_user(
                username=f'testuser{i}',
                password=f'testpassword{i}'
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_create_user_admin_user(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'username': 'newuser',
            'password': 'newpassword',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_user_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'username': 'newuser',
            'password': 'newpassword',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PostListViewTestCase(APIRequestFactory):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.url = reverse('post-list')

    def test_list_posts_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_posts_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pagination(self):
        for i in range(15):
            Post.objects.create(
                title=f'Test Post {i}',
                content=f'Test content {i}',
                author=self.user
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_permission(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_filter(self):
        Post.objects.create(
            title='Search Test Post',
            content='Search test content',
            author=self.user,
            tags=['search-tag']
        )

        response = self.client.get(self.url, {'search': 'Search Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(self.url, {'search': 'search-tag'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        response = self.client.get(self.url, {'search': 'Non-existent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)


class TagViewSetTestCase(APIRequestFactory):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.url = reverse('tag-list')

    def test_list_tags_authenticated_user_with_api_key(self):
        api_key = 'your_api_key_here'
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {api_key}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_tags_authenticated_user_without_api_key(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pagination(self):
        for i in range(15):
            Tag.objects.create(name=f'Test Tag {i}')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)

    def test_permission(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PostViewSetTest(APIRequestFactory):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_post(self):
        url = '/api/posts/'
        data = {'title': 'Test Post', 'content': 'This is a test post.'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.get().title, 'Test Post')

    def test_publish_post(self):
        post = Post.objects.create(
            title='Draft Post', content='This is a draft post.', author=self.user
        )

        url = f'/api/posts/{post.id}/publish/'
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Post.objects.get().status,
                         Post.StatusChoices.Published)

    def test_archive_post(self):
        post = Post.objects.create(
            title='Published Post',
            content='This is a published post.',
            author=self.user,
            status=Post.StatusChoices.Published,
        )

        url = f'/api/posts/{post.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Post.objects.get().status, Post.StatusChoices.Draft)


class PostListViewTest(APIRequestFactory):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )
        self.api_key, _ = api_key_gen.objects.create_key(name="test_api_key")
        self.client.credentials(HTTP_X_API_KEY=self.api_key)

        # Create some test data (categories, posts, etc.)
        self.category = Category.objects.create(name='Test Category')
        self.post1 = Post.objects.create(
            title='Post 1',
            content='This is post 1 content.',
            author=self.user,
            category=self.category,
        )
        self.post2 = Post.objects.create(
            title='Post 2',
            content='This is post 2 content.',
            author=self.user,
            category=self.category,
        )

    def test_list_posts(self):
        url = '/api/postlist/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming two posts in the test data
        self.assertEqual(len(response.data['results']), 2)

    def test_search_posts(self):
        url = '/api/postlist/'
        response = self.client.get(url, {'search_param': 'Post 1'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Post 1')

    def test_order_posts(self):
        url = '/api/postlist/'
        response = self.client.get(url, {'ordering': 'created_at'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)


class CategoryViewSetTest(APIRequestFactory):
    def setUp(self):
        self.user = User.objects.create_user(
            username='adminuser', password='adminpassword', is_staff=True
        )
        self.api_key, _ = API_KEY_CUSTOM_HEADER.objects.create_key(
            name="test_api_key")
        self.client.credentials(HTTP_X_API_KEY=self.api_key)

    def test_create_category(self):
        url = '/api/categories/'
        data = {'name': 'Test Category'}

        # Ensure only admin users can create categories
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Log in as an admin user and try again
        self.client.login(username='adminuser', password='adminpassword')
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Category')


class LikeAPIViewTest(APIRequestFactory):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )
        self.post = Post.objects.create(
            title='Test Post', content='Test Content', author=self.user)

    def test_like_post(self):
        url = reverse('like-list')  # Adjust the URL based on your URL patterns
        data = {'post': self.post.id}

        # Ensure unauthorized user cannot like a post
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Log in and try again
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'success')
        self.assertEqual(response.data['data']['author'], self.user.id)
        self.assertEqual(response.data['data']['post'], self.post.id)


class UserProfileAPIViewTest(APIRequestFactory):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )

    def test_get_user_profile(self):
        # Adjust the URL based on your URL patterns
        url = reverse('user-profile', args=[self.user.id])

        # Ensure unauthorized user can access user profile
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_get_nonexistent_user_profile(self):
        non_existent_user_id = 999  # Assuming this user ID does not exist
        url = reverse('user-profile', args=[non_existent_user_id])

        # Ensure getting a profile for a non-existent user returns a 'User not found' message
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'User not found')
