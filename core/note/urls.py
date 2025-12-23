from django.urls import path
from .views import SolutionNoteView, SolutionNoteListView

urlpatterns = [
    path(
        "notes/list/",
        SolutionNoteListView.as_view(),
        name="solution_note_list",
    ),
    path(
        "notes/",
        SolutionNoteView.as_view(),
        name="solution_note",
    ),
]
