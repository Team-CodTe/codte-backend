from django.urls import path
from .views import RegisterProfileView

urlpatterns = [
    path("user/profile/", RegisterProfileView.as_view(), name="register_profile"),
]
