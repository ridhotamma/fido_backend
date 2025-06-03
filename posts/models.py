from django.db import models
from users.models import CustomUser
from media_utils import LocalMediaStorage, S3MediaStorage, ImageVariantMixin


class Post(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='posts'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"


class Comment(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='comments'
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} on {self.post.id}: {self.content[:30]}"


class Like(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='likes'
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"


class CommentLike(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id}"


class PostMedia(models.Model, ImageVariantMixin):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    file = models.ImageField(upload_to='post_media/', storage=LocalMediaStorage(), blank=True, null=True)
    file_sm = models.URLField(blank=True, null=True)
    file_md = models.URLField(blank=True, null=True)
    file_lg = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.file:
            from django.conf import settings
            if getattr(settings, 'DEBUG', True):
                storage = LocalMediaStorage()
            else:
                required = [
                    getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                    getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                    getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None),
                    getattr(settings, 'AWS_S3_REGION_NAME', None),
                ]
                if all(required):
                    storage = S3MediaStorage()
                else:
                    storage = LocalMediaStorage()
            base_path = f"post_media/{self.pk}/media"
            variants = self.generate_variants(self.file, storage, base_path)
            self.file_sm = variants.get('sm')
            self.file_md = variants.get('md')
            self.file_lg = variants.get('lg')
            super().save(update_fields=['file_sm', 'file_md', 'file_lg'])
