from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    recipient_username = serializers.CharField(
        source="recipient.username", read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "recipient_username",
            "sender",
            "sender_username",
            "notification_type",
            "post",
            "comment",
            "message",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "recipient",
            "sender",
            "notification_type",
            "post",
            "comment",
            "message",
        ]
