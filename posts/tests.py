from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from posts.models import Post, Comment

User = get_user_model()


class PostCommentTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='pass1234')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass1234')
        self.post = Post.objects.create(user=self.user1, content='Hello world!')
        self.comment_url = f'/api/posts/{self.post.id}/comments/create/'
        self.comment_list_url = f'/api/posts/{self.post.id}/comments/'

    def test_user_comment_on_post(self):
        self.client.force_authenticate(user=self.user2)
        data = {'content': 'Nice post!'}
        response = self.client.post(self.comment_url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 1)
        comment = Comment.objects.get(post=self.post)
        self.assertEqual(comment.content, 'Nice post!')
        self.assertEqual(comment.user, self.user2)

    def test_user_reply_with_mention(self):
        # user2 comments on post
        self.client.force_authenticate(user=self.user2)
        comment_data = {'content': 'Nice post!'}
        comment_resp = self.client.post(self.comment_url, comment_data, format='json')
        comment_id = comment_resp.data['id']
        # user1 replies to user2's comment with @mention
        self.client.force_authenticate(user=self.user1)
        reply_url = f'/api/posts/{self.post.id}/comments/{comment_id}/reply/'
        reply_data = {'content': '@user2 Thanks!'}
        reply_resp = self.client.post(reply_url, reply_data, format='json')
        self.assertEqual(reply_resp.status_code, 201)
        reply = Comment.objects.get(id=reply_resp.data['id'])
        self.assertEqual(reply.parent.id, comment_id)
        self.assertIn('@user2', reply.content)
        # Check mentions field in response
        self.assertIn('mentions', reply_resp.data)
        self.assertIn('user2', reply_resp.data['mentions'])


class PostCrudTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', email='user1@example.com', password='pass1234')
        self.client.force_authenticate(user=self.user)

    def test_create_post(self):
        url = '/api/posts/create/'
        data = {'content': 'My new post!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Post.objects.filter(content='My new post!').exists())

    def test_update_post(self):
        post = Post.objects.create(user=self.user, content='Old content')
        url = f'/api/posts/{post.id}/edit/'
        data = {'content': 'Updated content'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.content, 'Updated content')

    def test_delete_post(self):
        post = Post.objects.create(user=self.user, content='To be deleted')
        url = f'/api/posts/{post.id}/delete/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Post.objects.filter(id=post.id).exists())

    def test_archive_post(self):
        post = Post.objects.create(user=self.user, content='To be archived')
        url = f'/api/posts/{post.id}/archive/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertTrue(post.archived)
