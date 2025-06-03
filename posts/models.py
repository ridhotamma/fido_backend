from django.db import models
from users.models import CustomUser


class Post(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='posts'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

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
