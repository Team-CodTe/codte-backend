from django.urls import path
from .views import StudyDetailView

urlpatterns = [
    path(
        "studies/<int:id>/",
        StudyDetailView.as_view(),
        name="study_detail",
    ),
]
