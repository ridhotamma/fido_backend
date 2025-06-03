from rest_framework import serializers
from .models import Post, Comment


class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'user', 'content', 'created_at', 'archived', 'likes_count', 'likes']
        read_only_fields = ['id', 'user', 'created_at', 'archived', 'likes_count', 'likes']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_likes(self, obj):
        return [like.user.username for like in obj.likes.select_related('user').all()]


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False, allow_null=True)
    mentions = serializers.SerializerMethodField()
    post = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'created_at', 'parent', 'mentions']
        read_only_fields = ['id', 'user', 'created_at', 'mentions', 'post']

    def get_mentions(self, obj):
        import re
        usernames = re.findall(r'@([\w_]+)', obj.content)
        return usernames
