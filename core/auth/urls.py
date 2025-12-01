from django.urls import path
from .views import SocialLoginView

urlpatterns = [
    path("auth/login/<str:provider>/", SocialLoginView.as_view(), name="social_login"),
]
