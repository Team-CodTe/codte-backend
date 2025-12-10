from django.urls import path
from .views import StudyJoinView

urlpatterns = [
    path(
        "studies/join/",
        StudyJoinView.as_view(),
        name="study_join",
    ),
]
