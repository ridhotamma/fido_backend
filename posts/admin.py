from django.contrib import admin

from .models import Comment, CommentLike, Post, PostMedia, Tag

# Register your models here.
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(PostMedia)
admin.site.register(Tag)


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "comment", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "comment__content")
    raw_id_fields = ("user", "comment")
