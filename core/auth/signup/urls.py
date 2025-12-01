from django.urls import path
from .views import (
    SignUpView,
    UsernameValidationView,
    BojUsernameValidationView,
)

urlpatterns = [
    path("auth/signup/", SignUpView.as_view(), name="signup"),
    path(
        "auth/signup/validate/username/",
        UsernameValidationView.as_view(),
        name="signup_validate_username",
    ),
    path(
        "auth/signup/validate/boj/",
        BojUsernameValidationView.as_view(),
        name="signup_validate_boj",
    ),
]
