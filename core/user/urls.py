from django.urls import path
from .views import (
    UserMeView,
    UserProfileView,
    UsernameValidationView,
    BojUsernameValidationView,
)

urlpatterns = [
    path(
        "user/me/",
        UserMeView.as_view(),
        name="user_me",
    ),
    path(
        "user/profile/",
        UserProfileView.as_view(),
        name="user_profile",
    ),
    path(
        "user/validate/username/",
        UsernameValidationView.as_view(),
        name="validate_username",
    ),
    path(
        "user/validate/boj/",
        BojUsernameValidationView.as_view(),
        name="validate_boj_username",
    ),
]
