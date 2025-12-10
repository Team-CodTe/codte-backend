from django.urls import path
from .views import StudyListView

urlpatterns = [
    path(
        "studies/me/",
        StudyListView.as_view(),
        name="study_list",
    ),
]
