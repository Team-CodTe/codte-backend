from django.urls import path
from django.conf import settings
from .views import SocialLoginView, LogoutView, TokenRefreshView, TestLoginView

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

# DEBUG 모드에서만 테스트 로그인 엔드포인트 추가
if settings.DEBUG:
    urlpatterns += [
        path(
            "auth/test-login/",
            TestLoginView.as_view(),
            name="test_login",
        ),
    ]
