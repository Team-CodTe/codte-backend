from rest_framework import permissions
from core.models import Study, StudyMember


class IsStudyOwner(permissions.BasePermission):
    """
    스터디 소유자만 접근 가능한 권한
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Study):
            return obj.owner == request.user

        return False


class IsStudyMember(permissions.BasePermission):
    """
    스터디 멤버만 접근 가능한 권한
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Study):
            return StudyMember.objects.filter(study=obj, user=request.user).exists()

        return False
