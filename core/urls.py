from django.urls import include, path

urlpatterns = [
    path("", include("core.auth.urls")),
    path("", include("core.user.urls")),
    path("", include("core.study.urls")),
]
