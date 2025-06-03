from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from media_utils import LocalMediaStorage, ImageVariantMixin, S3MediaStorage


class CustomUser(AbstractUser, ImageVariantMixin):
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, storage=LocalMediaStorage())
    avatar_sm = models.URLField(blank=True, null=True)
    avatar_md = models.URLField(blank=True, null=True)
    avatar_lg = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.avatar:
            # Always use LocalMediaStorage in development
            if getattr(settings, 'DEBUG', True):
                storage = LocalMediaStorage()
            else:
                # Only use S3MediaStorage if all required AWS settings are present
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
            base_path = f"avatars/{self.pk}/avatar"
            variants = self.generate_variants(self.avatar, storage, base_path)
            self.avatar_sm = variants.get('sm')
            self.avatar_md = variants.get('md')
            self.avatar_lg = variants.get('lg')
            super().save(update_fields=['avatar_sm', 'avatar_md', 'avatar_lg'])

    def __str__(self):
        return self.username


class Follow(models.Model):
    follower = models.ForeignKey('CustomUser', related_name='following_set', on_delete=models.CASCADE)
    following = models.ForeignKey('CustomUser', related_name='followers_set', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
