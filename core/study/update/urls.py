from django.urls import path
from .views import StudyUpdateView

urlpatterns = [
    path(
        "studies/<int:id>/",
        StudyUpdateView.as_view(),
        name="study_update",
    ),
]
