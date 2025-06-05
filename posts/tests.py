from io import BytesIO

from django.contrib.auth import get_user_model
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from notifications.models import Notification
from posts.models import Comment, Post, Tag

User = get_user_model()


class PostCommentTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="pass1234"
        )
        self.post = Post.objects.create(user=self.user1, content="Hello world!")
        self.comment_url = f"/api/posts/{self.post.id}/comments/create/"
        self.comment_list_url = f"/api/posts/{self.post.id}/comments/"

    def test_user_comment_on_post(self):
        self.client.force_authenticate(user=self.user2)
        data = {"content": "Nice post!"}
        response = self.client.post(self.comment_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.filter(post=self.post).count(), 1)
        comment = Comment.objects.get(post=self.post)
        self.assertEqual(comment.content, "Nice post!")
        self.assertEqual(comment.user, self.user2)

    def test_user_reply_with_mention(self):
        # user2 comments on post
        self.client.force_authenticate(user=self.user2)
        comment_data = {"content": "Nice post!"}
        comment_resp = self.client.post(self.comment_url, comment_data, format="json")
        comment_id = comment_resp.data["id"]
        # user1 replies to user2's comment with @mention
        self.client.force_authenticate(user=self.user1)
        reply_url = f"/api/posts/{self.post.id}/comments/{comment_id}/reply/"
        reply_data = {"content": "@user2 Thanks!"}
        reply_resp = self.client.post(reply_url, reply_data, format="json")
        self.assertEqual(reply_resp.status_code, 201)
        reply = Comment.objects.get(id=reply_resp.data["id"])
        self.assertEqual(reply.parent.id, comment_id)
        self.assertIn("@user2", reply.content)
        # Check mentions field in response
        self.assertIn("mentions", reply_resp.data)
        self.assertIn("user2", reply_resp.data["mentions"])


class PostCrudTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass1234"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_post(self):
        url = "/api/posts/create/"
        data = {"content": "My new post!"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Post.objects.filter(content="My new post!").exists())

    def test_update_post(self):
        post = Post.objects.create(user=self.user, content="Old content")
        url = f"/api/posts/{post.id}/edit/"
        data = {"content": "Updated content"}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.content, "Updated content")

    def test_delete_post(self):
        post = Post.objects.create(user=self.user, content="To be deleted")
        url = f"/api/posts/{post.id}/delete/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Post.objects.filter(id=post.id).exists())

    def test_archive_post(self):
        post = Post.objects.create(user=self.user, content="To be archived")
        url = f"/api/posts/{post.id}/archive/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertTrue(post.archived)


class PostMediaUploadTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass1234"
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.post = Post.objects.create(user=self.user, content="A post with media")

    def test_upload_post_media_and_variants(self):
        url = reverse("post_media_upload", args=[self.post.id])
        img = Image.new("RGB", (800, 800), color=(120, 120, 120))
        img_io = BytesIO()
        img.save(img_io, "JPEG")
        img_io.seek(0)
        img_io.name = "media1.jpg"
        data = {"file": img_io}
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.post.refresh_from_db()
        self.assertEqual(self.post.media.count(), 1)
        media = self.post.media.first()
        self.assertIsNotNone(media.file_sm)
        self.assertIsNotNone(media.file_md)
        self.assertIsNotNone(media.file_lg)
        self.assertIn("sm", media.file_sm)
        self.assertIn("md", media.file_md)
        self.assertIn("lg", media.file_lg)


class CommentLikeTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="clike1", email="clike1@example.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="clike2", email="clike2@example.com", password="pass1234"
        )
        self.post = Post.objects.create(
            user=self.user1, content="Post for comment like"
        )
        self.comment = Comment.objects.create(
            user=self.user2, post=self.post, content="Comment to like"
        )
        self.like_url = f"/api/posts/comments/{self.comment.id}/like/"
        self.unlike_url = f"/api/posts/comments/{self.comment.id}/unlike/"

    def test_user_can_like_comment(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.comment.likes.count(), 1)
        self.assertEqual(self.comment.likes.first().user, self.user1)

    def test_user_cannot_like_comment_twice(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.like_url)
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.comment.likes.count(), 1)

    def test_user_can_unlike_comment(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.like_url)
        response = self.client.post(self.unlike_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.comment.likes.count(), 0)

    def test_user_unlike_without_like(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.unlike_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.comment.likes.count(), 0)


class CommentLikeNotificationTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="notify1", email="notify1@example.com", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            username="notify2", email="notify2@example.com", password="pass1234"
        )
        self.post = Post.objects.create(
            user=self.user1, content="Post for notification"
        )
        self.comment = Comment.objects.create(
            user=self.user2, post=self.post, content="Comment to be liked"
        )
        self.like_url = f"/api/posts/comments/{self.comment.id}/like/"
        self.unlike_url = f"/api/posts/comments/{self.comment.id}/unlike/"

    def test_like_comment_creates_notification(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, 201)
        notif = Notification.objects.filter(
            recipient=self.user2,
            sender=self.user1,
            comment=self.comment,
            notification_type="like",
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn("liked your comment", notif.message)

    def test_unlike_comment_does_not_create_notification(self):
        self.client.force_authenticate(user=self.user1)
        self.client.post(self.like_url)
        Notification.objects.all().delete()  # Clear notifications
        response = self.client.post(self.unlike_url)
        self.assertEqual(response.status_code, 200)
        notif = Notification.objects.filter(
            recipient=self.user2,
            sender=self.user1,
            comment=self.comment,
            notification_type="like",
        ).first()
        self.assertIsNone(notif)


class TagAutocompleteTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="taguser", email="taguser@example.com", password="pass1234"
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        Tag.objects.create(name="pemilu2024", popularity=5)
        Tag.objects.create(name="kaburajadulu", popularity=10)
        Tag.objects.create(name="kabarbaik", popularity=7)

    def test_tag_autocomplete_by_query(self):
        resp = self.client.get("/api/posts/tags/autocomplete/?q=ka")
        self.assertEqual(resp.status_code, 200)
        names = [t["name"] for t in resp.data]
        self.assertIn("kaburajadulu", names)
        self.assertIn("kabarbaik", names)
        self.assertNotIn("pemilu2024", names)
        # Should be sorted by popularity desc
        self.assertTrue(names.index("kaburajadulu") < names.index("kabarbaik"))

    def test_tag_autocomplete_empty_query(self):
        resp = self.client.get("/api/posts/tags/autocomplete/")
        self.assertEqual(resp.status_code, 200)
        # Should return top tags by popularity
        names = [t["name"] for t in resp.data]
        self.assertEqual(names[0], "kaburajadulu")
        self.assertIn("pemilu2024", names)


class PostTagCreationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tagcreator", email="tagcreator@example.com", password="pass1234"
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_tags_created_from_content(self):
        data = {"content": "This is about #pemilu2024 and #kabarbaik"}
        resp = self.client.post("/api/posts/create/", data, format="json")
        self.assertEqual(resp.status_code, 201)
        post_id = resp.data["id"]
        post = Post.objects.get(id=post_id)
        tag_names = set(post.tags.values_list("name", flat=True))
        self.assertIn("pemilu2024", tag_names)
        self.assertIn("kabarbaik", tag_names)
        # Tags should be auto-created in DB
        self.assertTrue(Tag.objects.filter(name="pemilu2024").exists())
        self.assertTrue(Tag.objects.filter(name="kabarbaik").exists())

    def test_tags_created_from_tag_names_field(self):
        data = {"content": "No hashtag here", "tag_names": ["pemilu2024", "kabarbaik"]}
        resp = self.client.post("/api/posts/create/", data, format="json")
        self.assertEqual(resp.status_code, 201)
        post_id = resp.data["id"]
        post = Post.objects.get(id=post_id)
        tag_names = set(post.tags.values_list("name", flat=True))
        self.assertIn("pemilu2024", tag_names)
        self.assertIn("kabarbaik", tag_names)
