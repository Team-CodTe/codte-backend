from django.urls import include, path

urlpatterns = [
    path("", include("core.auth.urls")),
    path("", include("core.user.urls")),
    path("", include("core.study.urls")),
    path("", include("core.member.urls")),
    path("", include("core.assignments.urls")),
    path("", include("core.note.urls")),
    path("", include("core.problem_solving_status.urls")),
    path("", include("core.common.urls")),
]
