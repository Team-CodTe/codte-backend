from django.urls import path
from .views import (
    StudyMemberListView,
    StudyMemberKickView,
    StudyOwnerTransferView,
)

urlpatterns = [
    path(
        "studies/<int:study_id>/members/",
        StudyMemberListView.as_view(),
        name="study_member_list",
    ),
    path(
        "studies/<int:study_id>/members/<int:member_id>/",
        StudyMemberKickView.as_view(),
        name="study_member_kick",
    ),
    path(
        "studies/<int:study_id>/members/<int:member_id>/owner/",
        StudyOwnerTransferView.as_view(),
        name="study_owner_transfer",
    ),
]
