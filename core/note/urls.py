from django.urls import path
from .views import SolutionNoteView

urlpatterns = [
    path(
        "notes/",
        SolutionNoteView.as_view(),
        name="solution_note",
    ),
]
