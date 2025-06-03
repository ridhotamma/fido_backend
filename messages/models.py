from django.db import models

from media_utils import get_media_storage
from users.models import CustomUser


class Message(models.Model):
    sender = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="received_messages"
    )
    content = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="messages/images/", storage=get_media_storage(), blank=True, null=True
    )
    video = models.FileField(
        upload_to="messages/videos/", storage=get_media_storage(), blank=True, null=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}: {self.content[:30]}"
