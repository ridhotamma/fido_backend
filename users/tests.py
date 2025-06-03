from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from io import BytesIO
from PIL import Image


User = get_user_model()


class UserAuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.user_data = {
            'username': 'testuser',
            'full_name': 'Test User',
            'email': 'testuser@example.com',
            'phone_number': '08123456789',
            'password': 'TestPassword123!'
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_login_with_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_data = {'email_or_phone': self.user_data['email'], 'password': self.user_data['password']}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_phone(self):
        self.client.post(self.register_url, self.user_data, format='json')
        login_data = {'email_or_phone': self.user_data['phone_number'], 'password': self.user_data['password']}
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_follow_and_unfollow(self):
        # Register two users
        user1_data = self.user_data
        user2_data = {
            'username': 'testuser2',
            'full_name': 'Test User2',
            'email': 'testuser2@example.com',
            'phone_number': '08123456780',
            'password': 'TestPassword123!'
        }
        self.client.post(self.register_url, user1_data, format='json')
        self.client.post(self.register_url, user2_data, format='json')

        # Login as user1
        login_data = {'email_or_phone': user1_data['email'], 'password': user1_data['password']}
        response = self.client.post(self.login_url, login_data, format='json')
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Get user2's id
        from users.models import CustomUser
        user2 = CustomUser.objects.get(email=user2_data['email'])

        # Follow user2
        follow_url = reverse('follow_user', args=[user2.id])
        response = self.client.post(follow_url)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Now following', response.data['detail'])

        # Check followers of user2
        followers_url = reverse('followers_list', args=[user2.id])
        response = self.client.get(followers_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], user1_data['username'])

        # Check following of user1
        following_url = reverse('following_list', args=[self.client.handler._force_user.id])
        response = self.client.get(following_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], user2_data['username'])

        # Unfollow user2
        unfollow_url = reverse('unfollow_user', args=[user2.id])
        response = self.client.post(unfollow_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Unfollowed', response.data['detail'])

        # Check followers of user2 again
        response = self.client.get(followers_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)


class UserProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', email='user1@example.com', password='pass1234')
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_update_user_profile(self):
        url = reverse('profile_update')
        data = {'first_name': 'Updated', 'last_name': 'User'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'User')

    def test_upload_avatar_and_variants(self):
        url = reverse('profile_upload_avatar')
        # Create a simple image in memory
        img = Image.new('RGB', (600, 600), color=(73, 109, 137))
        img_io = BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        img_io.name = 'test.jpg'  # Set a name attribute for the file
        data = {'avatar': img_io}
        response = self.client.post(url, data, format='multipart')
        print('UPLOAD RESPONSE:', response.status_code, response.data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        # Check all avatar variants are present
        self.assertIsNotNone(self.user.avatar_sm)
        self.assertIsNotNone(self.user.avatar_md)
        self.assertIsNotNone(self.user.avatar_lg)
        # Optionally, check the URLs are correct format
        self.assertIn('sm', self.user.avatar_sm)
        self.assertIn('md', self.user.avatar_md)
        self.assertIn('lg', self.user.avatar_lg)
