from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

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
