from django.urls import path
from .views import (
    UsernameValidationView,
    BojUsernameValidationView,
)

urlpatterns = [
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
