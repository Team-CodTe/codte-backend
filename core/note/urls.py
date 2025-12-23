from django.urls import path
from .views import (
    SolutionNoteView,
    SolutionNoteListView,
    SolutionNoteDetailView,
    SolutionNoteTemplateView,
)

urlpatterns = [
    path(
        "notes/list/",
        SolutionNoteListView.as_view(),
        name="solution_note_list",
    ),
    path(
        "notes/template/<int:study_id>/",
        SolutionNoteTemplateView.as_view(),
        name="solution_note_template",
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
