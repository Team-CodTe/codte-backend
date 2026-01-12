from django.urls import path
from .views import (
    ProblemStatusUpdateView,
    ProblemStatusView,
    ProblemMembersStatusView,
    StatisticsView,
)

urlpatterns = [
    path(
        "studies/<int:study_id>/assignments/update/",
        ProblemStatusUpdateView.as_view(),
        name="problem_status_update",
    ),
    path(
        "studies/<int:study_id>/assignments/status/",
        ProblemStatusView.as_view(),
        name="problem_status",
    ),
    path(
        "studies/<int:study_id>/problems/<int:problem_id>/status/members/",
        ProblemMembersStatusView.as_view(),
        name="problem_members_status",
    ),
    path(
        "studies/<int:study_id>/statistics/",
        StatisticsView.as_view(),
        name="statistics",
    ),
]

