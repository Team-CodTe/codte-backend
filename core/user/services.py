from core.models import Study


class UserService:
    """사용자 관련 비즈니스 로직 서비스"""

    class StudyOwnerCannotDeleteError(Exception):
        """스터디장인 경우 탈퇴 불가 예외"""

        def __init__(self, study_names: list[str]):
            self.study_names = study_names
            super().__init__("스터디장인 스터디가 있어 탈퇴할 수 없습니다.")

    def delete_user(self, user):
        """
        사용자를 삭제합니다.

        스터디장인 경우 먼저 스터디장 권한을 위임해야 합니다.

        Args:
            user: 삭제할 사용자 인스턴스

        Returns:
            None

        Raises:
            StudyOwnerCannotDeleteError: 스터디장인 경우
        """
        # 스터디 오너인 경우 탈퇴 불가
        owned_studies = Study.objects.filter(owner=user)
        if owned_studies.exists():
            study_names = list(owned_studies.values_list("name", flat=True))
            raise self.StudyOwnerCannotDeleteError(study_names)

        # 사용자 삭제
        user.delete()
