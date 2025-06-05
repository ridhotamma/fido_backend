from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification
from notifications.views import send_realtime_notification

from .models import Comment, CommentLike, Post, PostLike, Tag
from .serializers import CommentSerializer, PostMediaSerializer, PostSerializer, TagSerializer


class PostCreateView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PostUpdateView(generics.UpdateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()

    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs["pk"], user=self.request.user)


class PostDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()

    def get_object(self):
        return get_object_or_404(Post, pk=self.kwargs["pk"], user=self.request.user)


class PostArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, user=request.user)
        post.archived = True
        post.save()
        return Response({"detail": "Post archived."}, status=status.HTTP_200_OK)


class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        parent = None
        if "parent_id" in self.kwargs:
            parent = get_object_or_404(Comment, pk=self.kwargs["parent_id"])
        comment = serializer.save(user=self.request.user, post=post, parent=parent)
        # Notification for reply
        if parent and parent.user != self.request.user:
            notification = Notification.objects.create(
                recipient=parent.user,
                sender=self.request.user,
                notification_type="reply",
                post=post,
                comment=comment,
                message=f"{self.request.user.username} replied to your comment.",
            )
            send_realtime_notification(notification)


class CommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post_id = self.kwargs["post_id"]
        return Comment.objects.filter(post_id=post_id, parent=None).order_by(
            "created_at"
        )


class CommentReplyListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        parent_id = self.kwargs["parent_id"]
        return Comment.objects.filter(parent_id=parent_id).order_by("created_at")


class LikePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if not created:
            return Response(
                {"detail": "Already liked."}, status=status.HTTP_400_BAD_REQUEST
            )
        # Notification for like
        if post.user != request.user:
            notification = Notification.objects.create(
                recipient=post.user,
                sender=request.user,
                notification_type="like",
                post=post,
                message=f"{request.user.username} liked your post.",
            )
            send_realtime_notification(notification)
        return Response({"detail": "Post liked."}, status=status.HTTP_201_CREATED)


class UnlikePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        deleted, _ = PostLike.objects.filter(user=request.user, post=post).delete()
        if deleted:
            return Response({"detail": "Post unliked."}, status=status.HTTP_200_OK)
        return Response(
            {"detail": "You have not liked this post."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PostMediaUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id, user=request.user)
        serializer = PostMediaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post)
            post.refresh_from_db()
            return Response(PostSerializer(post).data, status=201)
        return Response(serializer.errors, status=400)


class LikeCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        like, created = CommentLike.objects.get_or_create(
            user=request.user, comment=comment
        )
        if not created:
            return Response(
                {"detail": "Already liked."}, status=status.HTTP_400_BAD_REQUEST
            )
        # Notification for comment like
        if comment.user != request.user:
            notification = Notification.objects.create(
                recipient=comment.user,
                sender=request.user,
                notification_type="like",
                post=comment.post,
                comment=comment,
                message=f"{request.user.username} liked your comment.",
            )
            send_realtime_notification(notification)
        return Response({"detail": "Comment liked."}, status=status.HTTP_201_CREATED)


class UnlikeCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        deleted, _ = CommentLike.objects.filter(
            user=request.user, comment=comment
        ).delete()
        if deleted:
            return Response({"detail": "Comment unliked."}, status=status.HTTP_200_OK)
        return Response(
            {"detail": "You have not liked this comment."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TagAutocompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.GET.get("q", "").strip().lower()
        tags = Tag.objects.all()
        if q:
            tags = tags.filter(name__icontains=q)
        tags = tags.order_by("-popularity", "name")[:10]
        return Response(TagSerializer(tags, many=True).data)
