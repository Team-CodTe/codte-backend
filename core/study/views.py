from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Subquery, OuterRef
from drf_spectacular.utils import extend_schema

from core.models import Study, StudyMember, StudyRole
from .serializers import (
    StudyCreateSerializer,
    StudyCreateErrorSerializer,
    StudyDetailSerializer,
    StudyUpdateSerializer,
    StudyJoinSerializer,
    StudyJoinResponseSerializer,
    StudyListSerializer,
    StudyMemberListSerializer,
)
from core.common.serializers import ErrorEnvelopeSerializer
from .services import (
    StudyService,
    StudyMemberService,
)
from .permissions import IsStudyOwner, IsStudyMember


@extend_schema(tags=["studies"])
class StudyCreateView(APIView):
    """스터디 생성 API"""

    permission_classes = [IsAuthenticated]
    service_class = StudyService

    @extend_schema(
        summary="스터디 생성",
        description="새로운 스터디를 생성합니다. 생성자는 자동으로 스터디장이 됩니다.",
        request=StudyCreateSerializer,
        responses={
            201: StudyCreateSerializer,
            400: StudyCreateErrorSerializer,
        },
    )
    def post(self, request):
        serializer = StudyCreateSerializer(data=request.data)
        if serializer.is_valid():
            service = self.service_class()
            study = service.create_study_with_owner(
                owner=request.user, validated_data=serializer.validated_data
            )

            return Response(
                StudyCreateSerializer(study).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["studies"])
class StudyDetailView(APIView):
    """스터디 상세 조회, 수정, 삭제 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    def get_permissions(self):
        """HTTP 메서드에 따라 다른 권한 적용"""
        if self.request.method == "GET":
            return [IsAuthenticated(), IsStudyMember()]
        elif self.request.method == "PATCH":
            return [IsAuthenticated(), IsStudyOwner()]
        elif self.request.method == "DELETE":
            return [IsAuthenticated(), IsStudyOwner()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="스터디 상세 조회",
        description="스터디의 상세 정보를 조회합니다. 스터디 멤버만 조회 가능합니다.",
        responses={200: StudyDetailSerializer},
    )
    def get(self, request, study_id):
        study = get_object_or_404(
            Study.objects.annotate(
                current_user_role=Subquery(
                    StudyMember.objects.filter(
                        study=OuterRef("pk"), user=request.user
                    ).values("role")[:1]
                )
            ),
            id=study_id,
        )

        self.check_object_permissions(request, study)

        serializer = StudyDetailSerializer(study, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="스터디 정보 수정",
        description="스터디 정보를 수정합니다. 스터디장만 수정 가능합니다.",
        request=StudyUpdateSerializer,
        responses={200: StudyUpdateSerializer},
    )
    def patch(self, request, study_id):
        study = get_object_or_404(Study, id=study_id)

        self.check_object_permissions(request, study)

        serializer = StudyUpdateSerializer(study, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="스터디 삭제",
        description="스터디를 삭제합니다. 스터디장만 삭제 가능합니다.",
        responses={204: None},
    )
    def delete(self, request, study_id):
        study = get_object_or_404(Study, id=study_id)

        self.check_object_permissions(request, study)

        study.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["studies"])
class StudyJoinView(APIView):
    """스터디 가입 API"""

    permission_classes = [IsAuthenticated]
    service_class = StudyMemberService

    @extend_schema(
        summary="스터디 가입",
        description="초대 코드를 이용하여 스터디에 가입합니다.",
        request=StudyJoinSerializer,
        responses={
            201: StudyJoinResponseSerializer,
            400: ErrorEnvelopeSerializer,
        },
    )
    def post(self, request):
        serializer = StudyJoinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        invite_code = serializer.validated_data["invite_code"]

        try:
            service = self.service_class()
            study = service.join_study(user=request.user, invite_code=invite_code)
        except ValueError as e:
            return Response(
                {
                    "error_code": "ALREADY_MEMBER",
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": study.id,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["studies"])
class StudyLeaveView(APIView):
    """스터디 탈퇴 API"""

    permission_classes = [IsAuthenticated, IsStudyMember]

    @extend_schema(
        summary="스터디 탈퇴",
        description="현재 사용자가 스터디에서 탈퇴합니다. 스터디 오너는 탈퇴할 수 없습니다.",
        responses={
            204: None,
            400: ErrorEnvelopeSerializer,
        },
    )
    def delete(self, request, study_id):
        membership = get_object_or_404(
            StudyMember, study_id=study_id, user=request.user
        )

        if membership.role == StudyRole.OWNER:
            return Response(
                {
                    "error_code": "OWNER_CANNOT_LEAVE",
                    "message": "스터디 오너는 탈퇴할 수 없습니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["studies"])
class StudyListView(APIView):
    """가입한 스터디 목록 조회 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 스터디 목록 조회",
        description="현재 로그인한 사용자가 가입한 스터디 목록을 조회합니다.",
        responses={200: StudyListSerializer(many=True)},
    )
    def get(self, request):
        # 현재 사용자가 가입한 스터디 목록 조회 (N+1 쿼리 방지를 위해 annotate 사용)
        study_memberships = (
            StudyMember.objects.filter(user=request.user)
            .select_related("study")
            .annotate(member_count=Count("study__members"))
            .order_by("study__id")
        )

        serializer = StudyListSerializer(study_memberships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["studies"])
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


@extend_schema(tags=["studies"])
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


@extend_schema(tags=["studies"])
class StudyOwnerTransferView(APIView):
    """스터디장 위임 API"""

    permission_classes = [IsAuthenticated, IsStudyOwner]

    @extend_schema(
        summary="스터디장 위임",
        description="현재 스터디장이 다른 멤버에게 스터디장 권한을 위임합니다.",
        responses={
            200: None,
            400: ErrorEnvelopeSerializer,
            404: ErrorEnvelopeSerializer,
        },
    )
    def patch(self, request, study_id, member_id):
        study = get_object_or_404(Study, id=study_id)
        self.check_object_permissions(request, study)

        # 새 스터디장이 될 멤버 조회
        new_owner_membership = StudyMember.objects.filter(
            study_id=study_id, user_id=member_id
        ).first()

        if not new_owner_membership:
            return Response(
                {
                    "error_code": "MEMBER_NOT_FOUND",
                    "message": "해당 멤버를 찾을 수 없습니다.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 자기 자신에게 위임 불가
        if new_owner_membership.user_id == request.user.id:
            return Response(
                {
                    "error_code": "CANNOT_TRANSFER_TO_SELF",
                    "message": "자기 자신에게는 위임할 수 없습니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 현재 스터디장의 멤버십 조회
        current_owner_membership = StudyMember.objects.get(
            study_id=study_id, user=request.user
        )

        # 역할 교체
        current_owner_membership.role = StudyRole.MEMBER
        current_owner_membership.save()

        new_owner_membership.role = StudyRole.OWNER
        new_owner_membership.save()

        # Study.owner 업데이트
        study.owner = new_owner_membership.user
        study.save()

        return Response(
            {"message": "스터디장이 성공적으로 위임되었습니다."},
            status=status.HTTP_200_OK,
        )
