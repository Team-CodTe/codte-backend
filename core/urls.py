from django.urls import include, path

urlpatterns = [
    path("", include("core.auth.login.urls")),
    path("", include("core.auth.logout.urls")),
    path("", include("core.auth.refresh.urls")),
    path("", include("core.user.me.urls")),
    path("", include("core.user.profile.urls")),
    path("", include("core.user.validate.urls")),
    path("", include("core.study.join.urls")),
    path("", include("core.study.detail.urls")),
    path("", include("core.study.list.urls")),
    path("", include("core.study.create.urls")),
]
