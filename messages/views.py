from rest_framework import generics, permissions
from .models import Message
from .serializers import MessageSerializer
from notifications.models import Notification
from django.db.models import Q


# Create your views here.

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

    def perform_create(self, serializer):
        recipient_id = self.kwargs.get('user_id')
        recipient = None
        if recipient_id:
            from users.models import CustomUser
            recipient = CustomUser.objects.get(pk=recipient_id)
        serializer.save(sender=self.request.user, recipient=recipient)
        # Notification for receiving a message
        if recipient and recipient != self.request.user:
            Notification.objects.create(
                recipient=recipient,
                sender=self.request.user,
                notification_type='message',
                message=f"{self.request.user.username} sent you a message."
            )
