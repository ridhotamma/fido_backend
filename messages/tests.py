from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser
from .models import Message
from notifications.models import Notification
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from channels.testing import WebsocketCommunicator
from fido_web.asgi import application
import pytest
import json
import tempfile
import os


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


@pytest.mark.asyncio
class TestWebSocketRealtime:
    async def test_realtime_notification(self, db):
        from users.models import CustomUser
        from notifications.models import Notification
        user = CustomUser.objects.create_user(username='wsnotify', password='pass1234')
        communicator = WebsocketCommunicator(application, f"/ws/notifications/{user.id}/")
        connected, _ = await communicator.connect()
        assert connected
        notif = Notification.objects.create(
            recipient=user,
            sender=user,
            notification_type='like',
            message='WebSocket notification!'
        )
        from notifications.views import send_realtime_notification
        send_realtime_notification(notif)
        response = await communicator.receive_from()
        data = json.loads(response)
        assert data['message'] == 'WebSocket notification!'
        await communicator.disconnect()

    async def test_realtime_user_message(self, db):
        from users.models import CustomUser
        sender = CustomUser.objects.create_user(username='wssender', password='pass1234')
        recipient = CustomUser.objects.create_user(username='wsrecipient', password='pass1234')
        communicator = WebsocketCommunicator(application, f"/ws/chat/{recipient.id}/")
        communicator.scope['user'] = sender
        connected, _ = await communicator.connect()
        assert connected
        msg_data = {'content': 'Hello via WebSocket!'}
        await communicator.send_json_to(msg_data)
        response = await communicator.receive_from()
        data = json.loads(response)
        assert data['content'] == 'Hello via WebSocket!'
        await communicator.disconnect()


@pytest.mark.asyncio
class TestWebSocketRealtimeMessage:
    async def test_realtime_message_content_and_media(self, db):
        from users.models import CustomUser
        from .models import Message
        sender = CustomUser.objects.create_user(username='ws_sender', password='pass1234')
        recipient = CustomUser.objects.create_user(username='ws_recipient', password='pass1234')
        # Connect as recipient to their chat group
        communicator = WebsocketCommunicator(application, f"/ws/chat/{sender.id}/{recipient.id}/")
        communicator.scope['user'] = recipient
        connected, _ = await communicator.connect()
        assert connected
        # Create a message with content, image, and video
        msg = Message.objects.create(
            sender=sender,
            recipient=recipient,
            content='Hello with media!',
        )
        # Attach dummy image and video files
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_file:
            img_file.write(b'\xff\xd8\xff')  # minimal JPEG header
            img_file.flush()
            msg.image.save('test.jpg', open(img_file.name, 'rb'))
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as vid_file:
            vid_file.write(b'\x00\x00\x00\x18ftypmp42')  # minimal mp4 header
            vid_file.flush()
            msg.video.save('test.mp4', open(vid_file.name, 'rb'))
        msg.save()
        # Import and call the realtime function
        from .views import send_realtime_message
        send_realtime_message(msg)
        response = await communicator.receive_from()
        data = json.loads(response)
        assert data['id'] == msg.id
        assert data['sender'] == sender.username
        assert data['recipient'] == recipient.username
        assert data['content'] == 'Hello with media!'
        assert data['image'].endswith('.jpg')
        assert data['video'].endswith('.mp4')
        await communicator.disconnect()
        os.unlink(img_file.name)
        os.unlink(vid_file.name)
