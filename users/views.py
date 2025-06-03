from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Follow
from .serializers import (
    LoginByEmailOrPhoneSerializer,
    ProfilePictureSerializer,
    RegisterSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "User registered successfully"}, status=status.HTTP_201_CREATED
        )


class ProfileMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "bio": user.bio,
            "avatar": user.avatar.url if user.avatar else None,
            "phone_number": user.phone_number,
        }
        return Response(data)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        data = request.data
        # Update allowed fields
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.bio = data.get("bio", user.bio)
        user.phone_number = data.get("phone_number", user.phone_number)
        if "avatar" in data:
            user.avatar = data["avatar"]
        user.save()
        return Response({"message": "Profile updated successfully"})


class LoginByEmailOrPhoneView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginByEmailOrPhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            to_follow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)
        if to_follow == request.user:
            return Response({"detail": "You cannot follow yourself."}, status=400)
        follow, created = Follow.objects.get_or_create(
            follower=request.user, following=to_follow
        )
        if not created:
            return Response({"detail": "Already following."}, status=400)
        return Response({"detail": f"Now following {to_follow.username}."}, status=201)


class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            to_unfollow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)
        deleted, _ = Follow.objects.filter(
            follower=request.user, following=to_unfollow
        ).delete()
        if deleted:
            return Response(
                {"detail": f"Unfollowed {to_unfollow.username}."}, status=200
            )
        return Response({"detail": "You are not following this user."}, status=400)


class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        followers = Follow.objects.filter(following_id=user_id).select_related(
            "follower"
        )
        data = [
            {"id": f.follower.id, "username": f.follower.username} for f in followers
        ]
        return Response(data)


class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        following = Follow.objects.filter(follower_id=user_id).select_related(
            "following"
        )
        data = [
            {"id": f.following.id, "username": f.following.username} for f in following
        ]
        return Response(data)


class ProfilePictureUploadView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = ProfilePictureSerializer

    def post(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            request.user.refresh_from_db()
            return Response(
                {
                    "avatar": request.user.avatar.url if request.user.avatar else None,
                    "avatar_sm": request.user.avatar_sm,
                    "avatar_md": request.user.avatar_md,
                    "avatar_lg": request.user.avatar_lg,
                },
                status=200,
            )
        return Response(serializer.errors, status=400)
