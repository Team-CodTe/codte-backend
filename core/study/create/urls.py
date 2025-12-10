from django.urls import path
from .views import StudyCreateView

urlpatterns = [
    path(
        "studies/",
        StudyCreateView.as_view(),
        name="study_create",
    ),
]
