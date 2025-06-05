from django.db import models

from media_utils import ImageVariantMixin, get_media_storage
from users.models import CustomUser


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    popularity = models.PositiveIntegerField(default=0, db_index=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)
    tags = models.ManyToManyField("Tag", related_name="posts", blank=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"


class Comment(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="comments"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="replies", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.user.username} on {self.post.id}: {self.content[:30]}"


class PostLike(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="post_likes"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"


class CommentLike(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="comment_likes"
    )
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "comment")

    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id}"


class PostMedia(models.Model, ImageVariantMixin):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="media")
    file = models.ImageField(
        upload_to="post_media/", storage=get_media_storage(), blank=True, null=True
    )
    file_sm = models.URLField(blank=True, null=True)
    file_md = models.URLField(blank=True, null=True)
    file_lg = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file:
            storage = get_media_storage()
            base_path = f"post_media/{self.pk}/media"
            variants = self.generate_variants(self.file, storage, base_path)
            self.file_sm = variants.get("sm")
            self.file_md = variants.get("md")
            self.file_lg = variants.get("lg")
            super().save(update_fields=["file_sm", "file_md", "file_lg"])

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Post Media"
        verbose_name_plural = "Post Media"
