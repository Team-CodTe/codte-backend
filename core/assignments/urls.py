from django.urls import path
from .views import (
    CustomAssignmentAddView,
    DailyAssignmentView,
)

urlpatterns = [
    path(
        "studies/<int:study_id>/assignments/",
        DailyAssignmentView.as_view(),
        name="daily_assignments",
    ),
    path(
        "studies/<int:study_id>/assignments/custom/",
        CustomAssignmentAddView.as_view(),
        name="custom_assignment_add",
    ),
]
