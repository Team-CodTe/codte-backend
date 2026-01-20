from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from core.models import Study, StudyMember, StudyRole


class StudyService:
    """스터디 관련 비즈니스 로직 서비스"""

    def create_study_with_owner(self, owner, validated_data):
        """
        스터디를 생성하고 소유자를 멤버로 추가합니다.

        Args:
            owner: 스터디 소유자 (User 인스턴스)
            validated_data: serializer의 validated_data (dict)

        Returns:
            Study: 생성된 스터디 인스턴스
        """
        # 스터디 생성
        study = Study.objects.create(owner=owner, **validated_data)

        # 스터디 생성 시 owner를 StudyMember에 추가
        StudyMember.objects.create(
            study=study,
            user=owner,
            role=StudyRole.OWNER,
        )

        return study

    def join_study(self, user, invite_code):
        """
        초대 코드를 사용하여 스터디에 가입합니다.

        Args:
            user: 가입할 사용자 (User 인스턴스)
            invite_code: 스터디 초대 코드 (str)

        Returns:
            Study: 가입한 스터디 인스턴스

        Raises:
            Http404: 초대 코드에 해당하는 스터디가 없는 경우
            ValueError: 이미 가입된 스터디인 경우
        """
        # 초대 코드로 스터디 찾기
        study = get_object_or_404(Study, invite_code=invite_code)

        # 스터디 멤버로 추가
        try:
            StudyMember.objects.create(
                study=study,
                user=user,
                role=StudyRole.MEMBER,
            )
        except IntegrityError:
            raise ValueError("이미 가입된 스터디입니다.")

        return study
