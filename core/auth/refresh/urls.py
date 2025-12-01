from django.urls import path
from .views import TokenRefreshView

urlpatterns = [
    path(
        "auth/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
