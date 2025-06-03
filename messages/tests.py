from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser
from .models import Message
from notifications.models import Notification
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


class MessageNotificationTests(APITestCase):
    def setUp(self):
        self.sender = CustomUser.objects.create_user(username='sender', password='pass1234')
        self.recipient = CustomUser.objects.create_user(username='recipient', password='pass1234')
        self.client.force_authenticate(user=self.sender)
        self.send_url = reverse('message-send', kwargs={'user_id': self.recipient.id})

    def test_send_message_and_notification(self):
        data = {'content': 'Hello there!'}
        response = self.client.post(self.send_url, data, format='multipart')
        self.assertEqual(response.status_code, 201)
        # Message created
        msg = Message.objects.filter(sender=self.sender, recipient=self.recipient, content='Hello there!').first()
        self.assertIsNotNone(msg)
        # Notification created
        notif = Notification.objects.filter(
            recipient=self.recipient,
            sender=self.sender,
            notification_type='message',
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn('sent you a message', notif.message)

    def test_send_image_message_and_notification(self):
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img_io = BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        img_file = SimpleUploadedFile('test.jpg', img_io.read(), content_type='image/jpeg')
        data = {'image': img_file}
        response = self.client.post(self.send_url, data, format='multipart')
        self.assertEqual(response.status_code, 201)
        msg = Message.objects.filter(sender=self.sender, recipient=self.recipient, image__isnull=False).first()
        self.assertIsNotNone(msg)
        self.assertTrue(msg.image.name.endswith('.jpg'))
        notif = Notification.objects.filter(
            recipient=self.recipient,
            sender=self.sender,
            notification_type='message',
        ).first()
        self.assertIsNotNone(notif)
        # Recipient can retrieve the message with image
        self.client.force_authenticate(user=self.recipient)
        thread_url = reverse('message-thread', kwargs={'user_id': self.sender.id})
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(m['image'] for m in response.data))

    def test_send_video_message_and_notification(self):
        video_content = b'\x00\x00\x00\x18ftypmp42'  # minimal mp4 header
        video_file = SimpleUploadedFile('test.mp4', video_content, content_type='video/mp4')
        data = {'video': video_file}
        response = self.client.post(self.send_url, data, format='multipart')
        self.assertEqual(response.status_code, 201)
        msg = Message.objects.filter(sender=self.sender, recipient=self.recipient, video__isnull=False).first()
        self.assertIsNotNone(msg)
        self.assertTrue(msg.video.name.endswith('.mp4'))
        notif = Notification.objects.filter(
            recipient=self.recipient,
            sender=self.sender,
            notification_type='message',
        ).first()
        self.assertIsNotNone(notif)
        # Recipient can retrieve the message with video
        self.client.force_authenticate(user=self.recipient)
        thread_url = reverse('message-thread', kwargs={'user_id': self.sender.id})
        response = self.client.get(thread_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(m['video'] for m in response.data))
