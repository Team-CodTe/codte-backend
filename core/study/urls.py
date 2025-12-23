from django.urls import path
from .views import (
    DailyAssignmentView,
    StudyCreateView,
    StudyDetailView,
    StudyJoinView,
    StudyLeaveView,
    StudyListView,
)

urlpatterns = [
    path(
        "studies/",
        StudyCreateView.as_view(),
        name="study_create",
    ),
    path(
        "studies/join/",
        StudyJoinView.as_view(),
        name="study_join",
    ),
    path(
        "studies/me/",
        StudyListView.as_view(),
        name="study_list",
    ),
    path(
        "studies/<int:study_id>/",
        StudyDetailView.as_view(),
        name="study_detail",
    ),
    path(
        "studies/<int:study_id>/leave/",
        StudyLeaveView.as_view(),
        name="study_leave",
    ),
    path(
        "studies/<int:study_id>/daily-assignments/",
        DailyAssignmentView.as_view(),
        name="daily_assignments",
    ),
]
