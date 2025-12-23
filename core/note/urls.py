from django.urls import path
from .views import SolutionNoteCreateView

urlpatterns = [
    path(
        "notes/",
        SolutionNoteCreateView.as_view(),
        name="solution_note_create",
    ),
]
