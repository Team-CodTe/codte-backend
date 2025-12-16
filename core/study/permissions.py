from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from core.models import Study, StudyMember


class IsStudyOwner(permissions.BasePermission):
    """스터디 소유자만 접근 가능한 권한"""

    def has_permission(self, request, view):
        """요청이 스터디 소유자인지 확인"""
        if not request.user or not request.user.is_authenticated:
            return False

        # URL에서 study id를 가져옴
        study_id = view.kwargs.get("study_id")
        if not study_id:
            return False

        study = get_object_or_404(Study, id=study_id)
        return study.owner == request.user

    def has_object_permission(self, request, view, obj):
        """객체 레벨에서 스터디 소유자인지 확인"""
        if isinstance(obj, Study):
            return obj.owner == request.user
        return False


class IsStudyMember(permissions.BasePermission):
    """스터디 멤버만 접근 가능한 권한"""

    def has_permission(self, request, view):
        """요청이 스터디 멤버인지 확인"""
        if not request.user or not request.user.is_authenticated:
            return False

        # URL에서 study id를 가져옴
        study_id = view.kwargs.get("study_id")
        if not study_id:
            return False

        study = get_object_or_404(Study, id=study_id)
        return StudyMember.objects.filter(study=study, user=request.user).exists()

    def has_object_permission(self, request, view, obj):
        """객체 레벨에서 스터디 멤버인지 확인"""
        if isinstance(obj, Study):
            return StudyMember.objects.filter(study=obj, user=request.user).exists()
        return False
