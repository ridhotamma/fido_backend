from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


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
