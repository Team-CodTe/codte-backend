from django.urls import path
from .views import (
    StudyCreateView,
    StudyDetailView,
    StudyJoinView,
    StudyListView,
)

urlpatterns = [
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
        "studies/<int:id>/",
        StudyDetailView.as_view(),
        name="study_detail",
    ),
    path(
        "studies/",
        StudyCreateView.as_view(),
        name="study_create",
    ),
]
