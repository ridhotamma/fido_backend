from rest_framework import serializers

from .models import Comment, Post, PostMedia, Tag


class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ["id", "file", "file_sm", "file_md", "file_lg", "uploaded_at"]
        read_only_fields = ["id", "file_sm", "file_md", "file_lg", "uploaded_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "popularity"]
        read_only_fields = ["id", "popularity"]


class PostSerializer(serializers.ModelSerializer):
    media = PostMediaSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "created_at",
            "archived",
            "likes_count",
            "likes",
            "media",
            "tags",
            "tag_names",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "archived",
            "likes_count",
            "likes",
            "media",
            "tags",
        ]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_likes(self, obj):
        return [like.user.username for like in obj.likes.select_related("user").all()]

    def create(self, validated_data):
        tag_names = validated_data.pop("tag_names", [])
        post = super().create(validated_data)
        self._handle_tags(post, tag_names)
        return post

    def update(self, instance, validated_data):
        tag_names = validated_data.pop("tag_names", None)
        post = super().update(instance, validated_data)
        if tag_names is not None:
            self._handle_tags(post, tag_names)
        return post

    def _handle_tags(self, post, tag_names):
        import re
        tags = set(tag_names)
        # Also extract hashtags from content
        tags.update(re.findall(r"#(\w+)", post.content))
        tag_objs = []
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(name=tag.lower())
            if not created:
                tag_obj.popularity = tag_obj.posts.count()
                tag_obj.save(update_fields=["popularity"])
            tag_objs.append(tag_obj)
        post.tags.set(tag_objs)


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )
    mentions = serializers.SerializerMethodField()
    post = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user", "post", "content", "created_at", "parent", "mentions"]
        read_only_fields = ["id", "user", "created_at", "mentions", "post"]

    def get_mentions(self, obj):
        import re

        usernames = re.findall(r"@([\w_]+)", obj.content)
        return usernames
