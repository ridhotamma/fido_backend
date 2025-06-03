from rest_framework import generics, permissions
from .models import Message
from .serializers import MessageSerializer
from notifications.models import Notification
from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser
from notifications.views import send_realtime_notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_realtime_message(message):
    channel_layer = get_channel_layer()
    group_name = f"chat_{message.sender.id}_{message.recipient.id}"
    media = {}

    if hasattr(message, 'image') and message.image:
        media['image'] = message.image.url
    if hasattr(message, 'video') and message.video:
        media['video'] = message.video.url
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'chat.message',
            'message': {
                'id': message.id,
                'sender': message.sender.username,
                'recipient': message.recipient.username,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                **media
            }
        }
    )


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        other_user_id = self.kwargs.get('user_id')
        if other_user_id:
            return Message.objects.filter(
                (Q(sender=user) & Q(recipient_id=other_user_id)) |
                (Q(sender_id=other_user_id) & Q(recipient=user))
            ).order_by('created_at')
        return Message.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('-created_at')


class MessageSendView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        recipient_id = self.kwargs.get('user_id')
        recipient = None
        if recipient_id:
            from users.models import CustomUser
            recipient = CustomUser.objects.get(pk=recipient_id)
        serializer.save(sender=self.request.user, recipient=recipient)
        # Notification for receiving a message
        if recipient and recipient != self.request.user:
            notification = Notification.objects.create(
                recipient=recipient,
                sender=self.request.user,
                notification_type='message',
                message=f"{self.request.user.username} sent you a message."
            )
            send_realtime_notification(notification)
            # Real-time chat message
            last_message = Message.objects.filter(
                sender=self.request.user, recipient=recipient
            ).order_by('-created_at').first()
            if last_message:
                send_realtime_message(last_message)
