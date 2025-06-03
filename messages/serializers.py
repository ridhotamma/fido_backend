from rest_framework import serializers

from users.models import CustomUser

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    recipient_username = serializers.CharField(
        source="recipient.username", read_only=True
    )
    recipient = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), required=False
    )
    image = serializers.ImageField(required=False, allow_null=True)
    video = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sender_username",
            "recipient",
            "recipient_username",
            "content",
            "image",
            "video",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "sender", "sender_username"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipient"].required = False
