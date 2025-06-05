from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from .models import Follow, CoinClaimHistory
from .serializers import (
    LoginByEmailOrPhoneSerializer,
    ProfilePictureSerializer,
    RegisterSerializer,
)

User = get_user_model()


@extend_schema(
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description='User registered successfully',
            examples=[
                OpenApiExample(
                    name='Success Response',
                    value={'message': 'User registered successfully'},
                    status_codes=['201']
                ),
            ]
        ),
        400: OpenApiResponse(
            description='Validation Error',
            examples=[
                OpenApiExample(
                    name='Validation Error',
                    value={
                        'username': ['This username is already taken.'],
                        'email': ['This email is already registered.'],
                        'non_field_errors': ['You must provide either a username or an email.']
                    },
                    status_codes=['400']
                ),
            ]
        )
    },
    examples=[
        OpenApiExample(
            name='Register Example',
            value={
                'username': 'johndoe',
                'full_name': 'John Doe',
                'email': 'john@example.com',
                'phone_number': '+1234567890',
                'password': 'securePassword123'
            },
            request_only=True
        )
    ]
)
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

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description='Current user profile',
                examples=[
                    OpenApiExample(
                        name='Profile Response',
                        value={
                            "id": 1,
                            "username": "johndoe",
                            "email": "john@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "bio": "Software developer with passion for building amazing products",
                            "avatar": "/media/avatars/1/avatar.jpg",
                            "phone_number": "+1234567890",
                            "coins": 50
                        },
                        status_codes=['200']
                    ),
                ]
            ),
        }
    )
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
            "coins": user.coins,
        }
        return Response(data)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OpenApiExample(
            name='Profile Update Example',
            value={
                'first_name': 'John',
                'last_name': 'Doe',
                'bio': 'Software developer with passion for building amazing products',
                'phone_number': '+1234567890',
                'avatar': 'file_upload_field'
            },
            request_only=True
        ),
        responses={
            200: OpenApiResponse(
                description='Profile updated successfully',
                examples=[
                    OpenApiExample(
                        name='Success Response',
                        value={'message': 'Profile updated successfully'},
                        status_codes=['200']
                    ),
                ]
            ),
            400: OpenApiResponse(
                description='Bad Request',
                examples=[
                    OpenApiExample(
                        name='Bad Request Error',
                        value={'error': 'Invalid phone number format'},
                        status_codes=['400']
                    ),
                ]
            ),
        }
    )
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

    @extend_schema(
        request=LoginByEmailOrPhoneSerializer,
        responses={
            200: OpenApiResponse(
                description='Login successful',
                examples=[
                    OpenApiExample(
                        name='Success Response',
                        value={
                            'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                            'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
                        },
                        status_codes=['200']
                    ),
                ]
            ),
            400: OpenApiResponse(
                description='Login failed',
                examples=[
                    OpenApiExample(
                        name='Invalid Credentials',
                        value={'detail': 'Unable to log in with provided credentials.'},
                        status_codes=['400']
                    ),
                ]
            ),
        },
        examples=[
            OpenApiExample(
                name='Login with Email',
                value={
                    'email_or_phone': 'user@example.com',
                    'password': 'password123'
                },
                request_only=True
            ),
            OpenApiExample(
                name='Login with Phone',
                value={
                    'email_or_phone': '+1234567890',
                    'password': 'password123'
                },
                request_only=True
            ),
        ]
    )
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

    @extend_schema(
        request=OpenApiExample(
            name='Follow User Request',
            value={
                'user_id': 123
            },
            request_only=True
        ),
        responses={
            201: OpenApiResponse(
                description='Successfully followed user',
                examples=[
                    OpenApiExample(
                        name='Success Response',
                        value={'message': 'Now following username.'},
                        status_codes=['201']
                    ),
                ]
            ),
            400: OpenApiResponse(
                description='Bad Request',
                examples=[
                    OpenApiExample(
                        name='Already Following',
                        value={'message': 'Already following.'},
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        name='Self Follow',
                        value={'message': 'You cannot follow yourself.'},
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        name='Missing User ID',
                        value={'message': 'User ID is required.'},
                        status_codes=['400']
                    ),
                ]
            ),
            404: OpenApiResponse(
                description='User not found',
                examples=[
                    OpenApiExample(
                        name='User Not Found',
                        value={'message': 'User not found.'},
                        status_codes=['404']
                    ),
                ]
            ),
        }
    )
    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"message": "User ID is required."}, status=400)
            
        try:
            to_follow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=404)
        if to_follow == request.user:
            return Response({"message": "You cannot follow yourself."}, status=400)
        follow, created = Follow.objects.get_or_create(
            follower=request.user, following=to_follow
        )
        if not created:
            return Response({"message": "Already following."}, status=400)
        return Response({"message": f"Now following {to_follow.username}."}, status=201)


class UnfollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OpenApiExample(
            name='Unfollow User Request',
            value={
                'user_id': 123
            },
            request_only=True
        ),
        responses={
            200: OpenApiResponse(
                description='Successfully unfollowed user',
                examples=[
                    OpenApiExample(
                        name='Success Response',
                        value={'message': 'Unfollowed username.'},
                        status_codes=['200']
                    ),
                ]
            ),
            400: OpenApiResponse(
                description='Bad Request',
                examples=[
                    OpenApiExample(
                        name='Not Following',
                        value={'message': 'You are not following this user.'},
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        name='Missing User ID',
                        value={'message': 'User ID is required.'},
                        status_codes=['400']
                    ),
                ]
            ),
            404: OpenApiResponse(
                description='User not found',
                examples=[
                    OpenApiExample(
                        name='User Not Found',
                        value={'message': 'User not found.'},
                        status_codes=['404']
                    ),
                ]
            ),
        }
    )
    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"message": "User ID is required."}, status=400)
            
        try:
            to_unfollow = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found."}, status=404)
        deleted, _ = Follow.objects.filter(
            follower=request.user, following=to_unfollow
        ).delete()
        if deleted:
            return Response(
                {"message": f"Unfollowed {to_unfollow.username}."}, status=200
            )
        return Response({"message": "You are not following this user."}, status=400)


class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description='List of current user\'s followers',
                examples=[
                    OpenApiExample(
                        name='Followers List',
                        value=[
                            {
                                "id": 1,
                                "username": "user1"
                            },
                            {
                                "id": 2,
                                "username": "user2"
                            }
                        ],
                        status_codes=['200']
                    ),
                ]
            ),
        }
    )
    def get(self, request):
        followers = Follow.objects.filter(following=request.user).select_related(
            "follower"
        )
        data = [
            {"id": f.follower.id, "username": f.follower.username} for f in followers
        ]
        return Response(data)


class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description='List of users being followed by current user',
                examples=[
                    OpenApiExample(
                        name='Following List',
                        value=[
                            {
                                "id": 3,
                                "username": "user3"
                            },
                            {
                                "id": 4,
                                "username": "user4"
                            }
                        ],
                        status_codes=['200']
                    ),
                ]
            ),
        }
    )
    def get(self, request):
        following = Follow.objects.filter(follower=request.user).select_related(
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

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'avatar': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Avatar image file'
                    },
                },
                'required': ['avatar']
            }
        },
        responses={
            200: OpenApiResponse(
                description='Avatar uploaded successfully',
                examples=[
                    OpenApiExample(
                        name='Success Response',
                        value={
                            "avatar": "/media/avatars/user_123/avatar.jpg",
                            "avatar_sm": "https://example.com/media/avatars/user_123/avatar_sm.jpg",
                            "avatar_md": "https://example.com/media/avatars/user_123/avatar_md.jpg",
                            "avatar_lg": "https://example.com/media/avatars/user_123/avatar_lg.jpg"
                        },
                        status_codes=['200']
                    ),
                ]
            ),
            400: OpenApiResponse(
                description='Invalid request',
                examples=[
                    OpenApiExample(
                        name='Invalid Image',
                        value={'avatar': ['Invalid image format. Supported formats are PNG, JPG, JPEG.']},
                        status_codes=['400']
                    ),
                    OpenApiExample(
                        name='File Too Large',
                        value={'avatar': ['File size too large. Maximum file size is 5MB.']},
                        status_codes=['400']
                    ),
                ]
            ),
        }
    )
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


class DailyCoinClaimView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description='Coins claimed successfully',
                examples=[
                    OpenApiExample(
                        name='Success Response',
                        value={
                            "message": "10 coins claimed!",
                            "coins": 50
                        },
                        status_codes=['200']
                    ),
                ]
            ),
            400: OpenApiResponse(
                description='Already claimed',
                examples=[
                    OpenApiExample(
                        name='Already Claimed',
                        value={
                            "message": "You have already claimed your daily coins."
                        },
                        status_codes=['400']
                    ),
                ]
            ),
        }
    )
    def post(self, request):
        user = request.user
        today = timezone.now().date()
        if user.last_claimed == today:
            return Response(
                {"message": "You have already claimed your daily coins."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.coins += 10
        user.last_claimed = today
        user.save(update_fields=["coins", "last_claimed"])
        CoinClaimHistory.objects.create(user=user, amount=10)
        return Response(
            {"message": "10 coins claimed!", "coins": user.coins},
            status=status.HTTP_200_OK,
        )


class CoinClaimHistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description='Coin claim history',
                examples=[
                    OpenApiExample(
                        name='Claim History Response',
                        value=[
                            {
                                "id": 1,
                                "claimed_at": "2025-06-05T15:24:30Z",
                                "amount": 10
                            },
                            {
                                "id": 2,
                                "claimed_at": "2025-06-04T12:18:45Z",
                                "amount": 10
                            }
                        ],
                        status_codes=['200']
                    ),
                ]
            ),
        }
    )
    def get(self, request):
        claims = CoinClaimHistory.objects.filter(user=request.user)
        from .serializers import CoinClaimHistorySerializer

        serializer = CoinClaimHistorySerializer(claims, many=True)
        return Response(serializer.data)
