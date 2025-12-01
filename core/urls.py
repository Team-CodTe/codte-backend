from django.urls import include, path

urlpatterns = [
    path("", include("core.auth.login.urls")),
    path("", include("core.auth.refresh.urls")),
    path("", include("core.user.profile.urls")),
    path("", include("core.user.validate.urls")),
]
