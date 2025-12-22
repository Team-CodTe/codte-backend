from django.urls import path
from .views import SocialLoginView, LogoutView, TokenRefreshView

urlpatterns = [
    path(
        "auth/login/",
        SocialLoginView.as_view(),
        name="social_login",
    ),
    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "auth/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
