from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import DailyAssignment, Problem, Study, StudyMember, StudyRole
from core.utils.solvedac import SolvedAC

DAILY_ASSIGNMENT_REFRESH_COOLDOWN = 1800


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


class StudyMemberService:
    """스터디 멤버 관련 비즈니스 로직 서비스"""

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


class RefreshCooldownError(Exception):
    """강제 갱신 쿨다운 에러"""

    def __init__(self, next_available_at: datetime):
        self.next_available_at = next_available_at
        super().__init__(f"{next_available_at.isoformat()} 이후에 가능합니다.")


class DailyAssignmentService:
    """일일 문제 배정 서비스"""

    def __init__(self):
        self.solvedac_service = SolvedAC()

    def get_member_boj_usernames(self, study: Study) -> List[str]:
        """스터디 멤버들의 백준 닉네임 목록 조회"""
        return list(
            StudyMember.objects.filter(study=study)
            .exclude(user__boj_username__isnull=True)
            .exclude(user__boj_username="")
            .values_list("user__boj_username", flat=True)
        )

    def can_force_refresh(self, study: Study) -> tuple[bool, Optional[datetime]]:
        """강제 갱신 가능 여부 확인

        Returns:
            tuple: (갱신 가능 여부, 다음 갱신 가능 시간)
                   - 갱신 가능하면 (True, None)
                   - 갱신 불가능하면 (False, 다음 갱신 가능 시간)
        """
        if study.last_problem_refreshed_at is None:
            return True, None

        next_available_at = study.last_problem_refreshed_at + timedelta(
            seconds=DAILY_ASSIGNMENT_REFRESH_COOLDOWN
        )
        now = timezone.now()

        if now >= next_available_at:
            return True, None
        return False, next_available_at

    @transaction.atomic
    def assign_daily_problems(
        self,
        study: Study,
        target_date: Optional[date] = None,
        force_refresh: bool = False,
    ) -> List[DailyAssignment]:
        """스터디에 일일 문제 배정"""
        if target_date is None:
            target_date = date.today()

        # 이미 오늘 배정된 문제가 있는지 확인
        existing = DailyAssignment.objects.filter(
            study=study,
            assigned_date=target_date,
            is_custom=False,
        )

        if existing.exists():
            if not force_refresh:
                return list(existing)

            # 강제 갱신 쿨다운 체크
            can_refresh, next_available_at = self.can_force_refresh(study)
            if not can_refresh:
                raise RefreshCooldownError(next_available_at)

            # 기존 비커스텀 문제 삭제
            existing.delete()

        # 멤버들의 백준 닉네임 수집
        boj_usernames = self.get_member_boj_usernames(study)

        # 검색 쿼리 생성
        query = self.solvedac_service.build_search_query(
            tier_min=study.tier_min,
            tier_max=study.tier_max,
            min_solved=study.min_solved,
            max_solved=study.max_solved,
            exclude_usernames=boj_usernames,
        )

        # 문제 검색
        problems_data = self.solvedac_service.search_problems(
            query=query,
            count=study.daily_problem_count,
        )

        assignments = []
        for problem in problems_data:
            # Problem 저장 (이미 존재하면 업데이트)
            problem, _ = Problem.objects.update_or_create(
                boj_number=problem["problemId"],
                defaults={
                    "title": problem["titleKo"],
                    "tier": problem["level"],
                    "link": f"https://www.acmicpc.net/problem/{problem['problemId']}",
                },
            )

            # DailyAssignment 생성
            assignment, _ = DailyAssignment.objects.get_or_create(
                study=study,
                problem=problem,
                assigned_date=target_date,
                defaults={"is_custom": False},
            )
            assignments.append(assignment)

        # 강제 갱신 시 마지막 갱신 시간 업데이트
        if force_refresh:
            study.last_problem_refreshed_at = timezone.now()
            study.save(update_fields=["last_problem_refreshed_at"])

        return assignments

    def assign_all_studies(self, target_date: Optional[date] = None) -> dict:
        """모든 스터디에 일일 문제 배정"""
        if target_date is None:
            target_date = date.today()

        results = {}
        for study in Study.objects.all():
            try:
                assignments = self.assign_daily_problems(study, target_date)
                results[study.id] = {
                    "status": "success",
                    "study_name": study.name,
                    "count": len(assignments),
                }
            except Exception as e:
                results[study.id] = {
                    "status": "error",
                    "study_name": study.name,
                    "message": str(e),
                }

        return results

    def get_daily_assignments(
        self, study: Study, target_date: Optional[date] = None
    ) -> List[DailyAssignment]:
        """스터디의 일일 문제 조회"""
        if target_date is None:
            target_date = date.today()

        return list(
            DailyAssignment.objects.filter(
                study=study,
                assigned_date=target_date,
            ).select_related("problem")
        )
