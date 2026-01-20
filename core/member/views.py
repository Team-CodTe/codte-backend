from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from core.models import Study, StudyMember, StudyRole
from core.common.serializers import ErrorEnvelopeSerializer
from core.study.permissions import IsStudyOwner, IsStudyMember
from .serializers import StudyMemberListSerializer
from .services import StudyMemberService


@extend_schema(tags=["members"])
class StudyMemberListView(APIView):
    """스터디 멤버 목록 조회 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="스터디 멤버 목록 조회",
        description="스터디에 가입한 멤버 목록을 조회합니다. 스터디 멤버만 조회 가능합니다.",
        responses={200: StudyMemberListSerializer(many=True)},
    )
    def get(self, request, study_id):
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        members = (
            StudyMember.objects.filter(study=study)
            .select_related("user")
            .order_by("joined_at")
        )

        serializer = StudyMemberListSerializer(members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["members"])
class StudyMemberKickView(APIView):
    """스터디 멤버 강제 퇴출 API"""

    permission_classes = [IsAuthenticated, IsStudyOwner]

    @extend_schema(
        summary="스터디 멤버 강제 퇴출",
        description="스터디장이 특정 멤버를 스터디에서 강제 퇴출시킵니다. 스터디장 자신은 퇴출할 수 없습니다.",
        responses={
            204: None,
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request, study_id, member_id):
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        # 퇴출 대상 멤버 조회
        membership = StudyMember.objects.filter(
            study_id=study_id, user_id=member_id
        ).first()

        if not membership:
            return Response(
                {
                    "error_code": "MEMBER_NOT_FOUND",
                    "message": "해당 멤버를 찾을 수 없습니다.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 스터디장은 퇴출 불가
        if membership.role == StudyRole.OWNER:
            return Response(
                {
                    "error_code": "CANNOT_KICK_OWNER",
                    "message": "스터디장은 퇴출할 수 없습니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["members"])
class StudyOwnerTransferView(APIView):
    """스터디장 위임 API"""

    permission_classes = [IsAuthenticated, IsStudyOwner]
    service_class = StudyMemberService

    @extend_schema(
        summary="스터디장 위임",
        description="현재 스터디장이 다른 멤버에게 스터디장 권한을 위임합니다.",
        responses={
            204: None,
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def patch(self, request, study_id, member_id):
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        try:
            service = self.service_class()
            service.transfer_ownership(
                study=study,
                current_owner=request.user,
                new_owner_id=member_id,
            )
        except ValueError as e:
            error_code = str(e)
            if error_code == "MEMBER_NOT_FOUND":
                return Response(
                    {
                        "error_code": "MEMBER_NOT_FOUND",
                        "message": "해당 멤버를 찾을 수 없습니다.",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            elif error_code == "CANNOT_TRANSFER_TO_SELF":
                return Response(
                    {
                        "error_code": "CANNOT_TRANSFER_TO_SELF",
                        "message": "자기 자신에게는 위임할 수 없습니다.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(status=status.HTTP_204_NO_CONTENT)
