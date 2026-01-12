from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db import transaction
from django.utils import timezone

from core.models import (
    DailyAssignment,
    Problem,
    ProblemSolvingStatus,
    Study,
    StudyMember,
)
from core.utils.solvedac import SolvedAC

DAILY_ASSIGNMENT_REFRESH_COOLDOWN = 1800  # 30분
PROBLEM_STATUS_UPDATE_COOLDOWN = 300  # 5분


class DailyAssignmentService:
    """오늘의 추천 문제 배정 서비스"""

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
        """스터디에 오늘의 추천 문제 배정"""
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
        """스터디의 오늘의 추천 문제 조회"""
        if target_date is None:
            target_date = date.today()

        return list(
            DailyAssignment.objects.filter(
                study=study,
                assigned_date=target_date,
            ).select_related("problem")
        )

    @transaction.atomic
    def add_custom_assignment(self, study: Study, boj_number: int) -> DailyAssignment:
        """
        커스텀 문제 추가

        Args:
            study: 스터디
            boj_number: 백준 문제 번호

        Returns:
            생성된 DailyAssignment

        Raises:
            ProblemNotFoundError: 문제를 찾을 수 없는 경우
            AlreadyAssignedError: 이미 오늘 배정된 문제인 경우
        """
        target_date = date.today()

        # 이미 오늘 배정된 문제인지 확인
        existing = DailyAssignment.objects.filter(
            study=study,
            problem__boj_number=boj_number,
            assigned_date=target_date,
        ).exists()

        if existing:
            raise AlreadyAssignedError(boj_number)

        # Solved.ac API로 문제 정보 조회 (없으면 ProblemNotFoundError 발생)
        problem_data = self.solvedac_service.get_problem_by_id(boj_number)

        # Problem 저장 (이미 존재하면 업데이트)
        problem, _ = Problem.objects.update_or_create(
            boj_number=problem_data["problemId"],
            defaults={
                "title": problem_data["titleKo"],
                "tier": problem_data["level"],
                "link": f"https://www.acmicpc.net/problem/{problem_data['problemId']}",
            },
        )

        # DailyAssignment 생성 (is_custom=True)
        assignment = DailyAssignment.objects.create(
            study=study,
            problem=problem,
            assigned_date=target_date,
            is_custom=True,
        )

        return assignment


class RefreshCooldownError(Exception):
    """강제 갱신 쿨다운 에러"""

    def __init__(self, next_available_at: datetime):
        self.next_available_at = next_available_at
        super().__init__(f"{next_available_at.isoformat()} 이후에 가능합니다.")


class AlreadyAssignedError(Exception):
    """이미 배정된 문제 에러"""

    def __init__(self, boj_number: int):
        self.boj_number = boj_number
        super().__init__(
            f"{boj_number}번 문제는 이미 오늘 추천 목록에 있는 문제입니다."
        )


class ProblemSolvingStatusService:
    """문제 풀이 상태 관리 서비스"""

    def can_update_status(
        self, user, study: Study, target_date: Optional[date] = None
    ) -> tuple[bool, Optional[datetime]]:
        """상태 업데이트 가능 여부 확인 (5분 쿨다운)

        Args:
            user: 사용자
            study: 스터디
            target_date: 대상 날짜 (기본값: 오늘)

        Returns:
            tuple: (업데이트 가능 여부, 다음 업데이트 가능 시간)
                   - 업데이트 가능하면 (True, None)
                   - 업데이트 불가능하면 (False, 다음 업데이트 가능 시간)
        """
        if target_date is None:
            target_date = date.today()

        # 해당 날짜의 DailyAssignment 중 가장 최근 업데이트 시간 확인
        assignments = DailyAssignment.objects.filter(
            study=study, assigned_date=target_date
        )
        if not assignments.exists():
            return True, None

        # 해당 날짜의 문제들에 대한 사용자의 가장 최근 업데이트 시간 확인
        latest_status = (
            ProblemSolvingStatus.objects.filter(
                assignment__study=study,
                assignment__assigned_date=target_date,
                user=user,
            )
            .order_by("-last_updated_at")
            .first()
        )

        if latest_status is None:
            return True, None

        next_available_at = latest_status.last_updated_at + timedelta(
            seconds=PROBLEM_STATUS_UPDATE_COOLDOWN
        )
        now = timezone.now()

        if now >= next_available_at:
            return True, None
        return False, next_available_at
