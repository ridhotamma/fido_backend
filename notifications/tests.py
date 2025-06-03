from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from notifications.models import Notification
from posts.models import Comment, Post
from users.models import CustomUser


class NotificationSystemTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = CustomUser.objects.create_user(username="user1", password="pass")
        self.user2 = CustomUser.objects.create_user(username="user2", password="pass")
        self.user3 = CustomUser.objects.create_user(username="user3", password="pass")
        self.post = Post.objects.create(user=self.user1, content="Hello world!")

    def test_like_notification(self):
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            reverse("like-post", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(response.status_code, 201)
        notif = Notification.objects.filter(
            recipient=self.user1, notification_type="like"
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("liked your post", notif.message)

    def test_reply_notification(self):
        comment = Comment.objects.create(
            user=self.user1, post=self.post, content="Nice post!"
        )
        self.client.force_authenticate(user=self.user2)
        url = reverse(
            "comment-reply", kwargs={"post_id": self.post.id, "parent_id": comment.id}
        )
        response = self.client.post(url, {"content": "Thanks!"}, format="json")
        self.assertEqual(response.status_code, 201)
        notif = Notification.objects.filter(
            recipient=self.user1, notification_type="reply"
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("replied to your comment", notif.message)
