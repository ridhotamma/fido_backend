from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser
from .models import Message
from notifications.models import Notification


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
