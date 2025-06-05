from django.urls import path

from .views import (
    CommentCreateView,
    CommentListView,
    CommentReplyListView,
    LikeCommentView,
    LikePostView,
    PostArchiveView,
    PostCreateView,
    PostDeleteView,
    PostMediaUploadView,
    PostUpdateView,
    UnlikeCommentView,
    UnlikePostView,
    TagAutocompleteView,
)

urlpatterns = [
    path("create/", PostCreateView.as_view(), name="post_create"),
    path("<int:pk>/edit/", PostUpdateView.as_view(), name="post_edit"),
    path("<int:pk>/delete/", PostDeleteView.as_view(), name="post_delete"),
    path("<int:pk>/archive/", PostArchiveView.as_view(), name="post_archive"),
    path("<int:post_id>/comments/", CommentListView.as_view(), name="comment_list"),
    path(
        "<int:post_id>/comments/create/",
        CommentCreateView.as_view(),
        name="comment_create",
    ),
    path(
        "comments/<int:parent_id>/replies/",
        CommentReplyListView.as_view(),
        name="comment_reply_list",
    ),
    path(
        "<int:post_id>/comments/<int:parent_id>/reply/",
        CommentCreateView.as_view(),
        name="comment-reply",
    ),
    path("<int:post_id>/like/", LikePostView.as_view(), name="like-post"),
    path("<int:post_id>/unlike/", UnlikePostView.as_view(), name="post_unlike"),
    path(
        "<int:post_id>/media/upload/",
        PostMediaUploadView.as_view(),
        name="post_media_upload",
    ),
    path(
        "comments/<int:comment_id>/like/",
        LikeCommentView.as_view(),
        name="comment-like",
    ),
    path(
        "comments/<int:comment_id>/unlike/",
        UnlikeCommentView.as_view(),
        name="comment-unlike",
    ),
    path("tags/autocomplete/", TagAutocompleteView.as_view(), name="tag_autocomplete"),
]
