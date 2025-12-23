from django.urls import path
from .views import SolutionNoteView, SolutionNoteListView, SolutionNoteDetailView

urlpatterns = [
    path(
        "notes/list/",
        SolutionNoteListView.as_view(),
        name="solution_note_list",
    ),
    path(
        "notes/<int:note_id>/",
        SolutionNoteDetailView.as_view(),
        name="solution_note_detail",
    ),
    path(
        "notes/",
        SolutionNoteView.as_view(),
        name="solution_note",
    ),
]
