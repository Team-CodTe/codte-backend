from django.urls import path
from .views import (
    SolutionNoteView,
    SolutionNoteDetailView,
    SolutionNoteTemplateView,
    CodeReviewView,
)

urlpatterns = [
    path(
        "studies/<int:study_id>/notes/",
        SolutionNoteView.as_view(),
        name="solution_note",
    ),
    path(
        "studies/<int:study_id>/template/",
        SolutionNoteTemplateView.as_view(),
        name="solution_note_template",
    ),
    path(
        "notes/<int:note_id>/",
        SolutionNoteDetailView.as_view(),
        name="solution_note_detail",
    ),
    path(
        "notes/<int:note_id>/review/",
        CodeReviewView.as_view(),
        name="code_review",
    ),
]
