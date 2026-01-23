from django.db import transaction

from core.models import StudyMember, StudyRole


class StudyMemberService:
    """스터디 멤버 관련 비즈니스 로직 서비스"""

    def transfer_ownership(self, study, current_owner, new_owner_id):
        """
        스터디장 권한을 다른 멤버에게 위임합니다.

        Args:
            study: 스터디 인스턴스
            current_owner: 현재 스터디장 (User 인스턴스)
            new_owner_id: 새 스터디장이 될 멤버의 user_id

        Returns:
            None

        Raises:
            ValueError: 새 스터디장이 될 멤버가 없거나, 자기 자신에게 위임하려는 경우
        """
        # 새 스터디장이 될 멤버 조회
        new_owner_membership = StudyMember.objects.filter(
            study=study, user_id=new_owner_id
        ).first()

        if not new_owner_membership:
            raise ValueError("MEMBER_NOT_FOUND")

        # 자기 자신에게 위임 불가
        if new_owner_membership.user_id == current_owner.id:
            raise ValueError("CANNOT_TRANSFER_TO_SELF")

        # 현재 스터디장의 멤버십 조회
        current_owner_membership = StudyMember.objects.get(
            study=study, user=current_owner
        )

        # 스터디장 권한 위임
        with transaction.atomic():
            current_owner_membership.role = StudyRole.MEMBER
            current_owner_membership.save()

            new_owner_membership.role = StudyRole.OWNER
            new_owner_membership.save()

            # Study.owner 업데이트
            study.owner = new_owner_membership.user
            study.save()
