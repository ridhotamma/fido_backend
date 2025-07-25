from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CoinClaimHistoryListView,
    DailyCoinClaimView,
    FollowersListView,
    FollowingListView,
    FollowUserView,
    LoginByEmailOrPhoneView,
    ProfileMeView,
    ProfilePictureUploadView,
    ProfileUpdateView,
    RegisterView,
    UnfollowUserView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/me/", ProfileMeView.as_view(), name="profile_me"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile_update"),
    path("login/", LoginByEmailOrPhoneView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="jwt_refresh"),
    path("follow/<int:user_id>/", FollowUserView.as_view(), name="follow_user"),
    path("unfollow/<int:user_id>/", UnfollowUserView.as_view(), name="unfollow_user"),
    path("followers/<int:user_id>/", FollowersListView.as_view(), name="followers_list"),
    path("following/<int:user_id>/", FollowingListView.as_view(), name="following_list"),
    path(
        "profile/upload-avatar/",
        ProfilePictureUploadView.as_view(),
        name="profile_upload_avatar",
    ),
    path("claim-daily-coins/", DailyCoinClaimView.as_view(), name="claim_daily_coins"),
    path(
        "coin-claim-history/",
        CoinClaimHistoryListView.as_view(),
        name="coin_claim_history",
    ),
]
