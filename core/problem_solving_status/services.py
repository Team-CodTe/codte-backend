from datetime import date, datetime, timedelta
from typing import List, Optional

from django.db import transaction
from django.utils import timezone

from core.models import (
    DailyAssignment,
    ProblemSolvingStatus,
    ProblemStatus,
    SolutionNote,
    Study,
    StudyMember,
)
from core.utils.solvedac import SolvedAC

PROBLEM_STATUS_UPDATE_COOLDOWN = 300  # 5분


class UpdateCooldownError(Exception):
    """상태 업데이트 쿨다운 에러"""

    def __init__(self, next_available_at: datetime):
        self.next_available_at = next_available_at
        super().__init__(f"5분 후에 다시 시도해주세요.")


class ProblemSolvingStatusService:
    """문제 풀이 상태 관리 서비스"""

    def __init__(self):
        self.solvedac_service = SolvedAC()

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


    @transaction.atomic
    def update_solving_status(
        self,
        user,
        study_id: int,
        target_date: Optional[date] = None,
    ) -> List[ProblemSolvingStatus]:
        """오늘의 추천 문제 풀이 상태 일괄 업데이트 (백준 API로 자동 확인)

        Args:
            user: 사용자
            study_id: 스터디 ID
            target_date: 대상 날짜 (기본값: 오늘)

        Returns:
            List[ProblemSolvingStatus]: 업데이트된 상태 목록

        Raises:
            UpdateCooldownError: 5분 쿨다운이 지나지 않은 경우
            ValueError: 사용자의 백준 사용자명이 없는 경우
        """
        if target_date is None:
            target_date = date.today()

        # 스터디 조회
        study = Study.objects.get(id=study_id)

        # 쿨다운 체크
        can_update, next_available_at = self.can_update_status(
            user, study, target_date
        )
        if not can_update:
            raise UpdateCooldownError(next_available_at)

        # 사용자의 백준 사용자명 확인
        if not user.boj_username:
            raise ValueError("백준 사용자명이 설정되지 않았습니다.")

        # 해당 날짜의 모든 DailyAssignment 조회
        assignments = DailyAssignment.objects.filter(
            study=study, assigned_date=target_date
        ).select_related("problem")

        if not assignments.exists():
            return []

        # 문제 ID 리스트 수집
        problem_ids = [assignment.problem.boj_number for assignment in assignments]

        # 백준 API로 여러 문제를 한 번에 확인
        solved_problems = self.solvedac_service.check_user_solved_problems(
            user.boj_username, problem_ids
        )

        # 각 assignment에 대해 풀이 상태 확인 후 업데이트
        updated_statuses = []
        for assignment in assignments:
            problem_id = assignment.problem.boj_number
            is_solved = solved_problems.get(problem_id, False)

            # 풀이 여부에 따라 상태 설정
            if is_solved:
                status = ProblemStatus.COMPLETED
            else:
                status = ProblemStatus.NOT_ATTEMPTED

            status_obj, created = ProblemSolvingStatus.objects.update_or_create(
                assignment=assignment,
                user=user,
                defaults={"status": status},
            )
            updated_statuses.append(status_obj)

        return updated_statuses

    def get_solving_statuses(
        self,
        user,
        study_id: int,
        target_date: Optional[date] = None,
        view: str = "me",
    ):
        """문제 풀이 상태 조회

        Args:
            user: 조회하는 사용자
            study_id: 스터디 ID
            target_date: 대상 날짜 (기본값: 오늘)
            view: 조회 방식 ('me' 또는 'group', 기본값: 'me')

        Returns:
            dict: 조회 결과 (view에 따라 구조가 다름)
        """
        if target_date is None:
            target_date = date.today()

        # 스터디 조회
        study = Study.objects.get(id=study_id)

        # 해당 날짜의 모든 DailyAssignment 조회
        assignments = DailyAssignment.objects.filter(
            study=study, assigned_date=target_date
        ).select_related("problem").order_by("problem__boj_number")

        if view == "me":
            return self._get_my_solving_statuses(user, study, assignments, target_date)
        elif view == "group":
            return self._get_group_solving_statuses(study, assignments, target_date)
        else:
            raise ValueError(f"잘못된 view 값입니다: {view}")

    def _get_my_solving_statuses(
        self, user, study, assignments, target_date
    ) -> dict:
        """현재 사용자의 문제 풀이 상태 조회"""
        if not assignments.exists():
            return {
                "date": target_date.isoformat(),
                "view": "me",
                "assignments": [],
                "total_count": 0,
                "problem_status_summary": {
                    "not_attempted_count": 0,
                    "in_progress_count": 0,
                    "completed_count": 0,
                },
                "note_status_summary": {
                    "not_completed_count": 0,
                    "completed_count": 0,
                },
                "can_update": True,
                "next_available_at": None,
            }

        # 사용자의 ProblemSolvingStatus 조회
        statuses = ProblemSolvingStatus.objects.filter(
            assignment__in=assignments, user=user
        ).select_related("assignment", "assignment__problem")

        # status를 assignment_id로 매핑
        status_dict = {status.assignment_id: status for status in statuses}

        # 사용자의 SolutionNote 조회 (note_status 확인용)
        solution_notes = SolutionNote.objects.filter(
            study=study, user=user, problem__in=[a.problem for a in assignments]
        ).select_related("problem")

        # note를 problem_id로 매핑
        note_dict = {note.problem_id: note for note in solution_notes}

        # 쿨다운 체크
        can_update, next_available_at = self.can_update_status(user, study, target_date)

        # assignments를 순회하며 상태 정보 구성
        assignment_list = []
        problem_status_counts = {
            "not_attempted_count": 0,
            "in_progress_count": 0,
            "completed_count": 0,
        }
        note_status_counts = {"not_completed_count": 0, "completed_count": 0}

        for assignment in assignments:
            status = status_dict.get(assignment.id)
            note = note_dict.get(assignment.problem_id)

            problem_status = (
                status.status if status else ProblemStatus.NOT_ATTEMPTED
            )
            note_status = "completed" if note else "not_completed"

            assignment_list.append(
                {
                    "problem_id": assignment.problem_id,
                    "boj_number": assignment.problem.boj_number,
                    "title": assignment.problem.title,
                    "problem_status": problem_status,
                    "note_status": note_status,
                    "last_updated_at": (
                        status.last_updated_at.isoformat() if status else None
                    ),
                }
            )

            # 카운트 증가
            if problem_status == ProblemStatus.NOT_ATTEMPTED:
                problem_status_counts["not_attempted_count"] += 1
            elif problem_status == ProblemStatus.IN_PROGRESS:
                problem_status_counts["in_progress_count"] += 1
            elif problem_status == ProblemStatus.COMPLETED:
                problem_status_counts["completed_count"] += 1

            if note_status == "not_completed":
                note_status_counts["not_completed_count"] += 1
            else:
                note_status_counts["completed_count"] += 1

        return {
            "date": target_date.isoformat(),
            "view": "me",
            "assignments": assignment_list,
            "total_count": len(assignment_list),
            "problem_status_summary": problem_status_counts,
            "note_status_summary": note_status_counts,
            "can_update": can_update,
            "next_available_at": (
                next_available_at.isoformat() if next_available_at else None
            ),
        }

    def _get_group_solving_statuses(self, study, assignments, target_date) -> dict:
        """모든 멤버의 문제 풀이 상태 조회 (그룹 조회)"""
        if not assignments.exists():
            return {
                "date": target_date.isoformat(),
                "view": "group",
                "members": [],
                "total_members": 0,
                "overall_summary": {
                    "problem_status_summary": {
                        "not_attempted_count": 0,
                        "in_progress_count": 0,
                        "completed_count": 0,
                        "total": 0,
                    },
                    "note_status_summary": {
                        "not_completed_count": 0,
                        "completed_count": 0,
                        "total": 0,
                    },
                },
            }

        # 스터디 멤버 조회
        members = StudyMember.objects.filter(study=study).select_related("user")

        # 모든 멤버의 ProblemSolvingStatus 조회
        statuses = ProblemSolvingStatus.objects.filter(
            assignment__in=assignments
        ).select_related("assignment", "assignment__problem", "user")

        # status를 (assignment_id, user_id)로 매핑
        status_dict = {
            (status.assignment_id, status.user_id): status for status in statuses
        }

        # 모든 멤버의 SolutionNote 조회
        solution_notes = SolutionNote.objects.filter(
            study=study, problem__in=[a.problem for a in assignments]
        ).select_related("problem", "user")

        # note를 (problem_id, user_id)로 매핑
        note_dict = {
            (note.problem_id, note.user_id): note for note in solution_notes
        }

        # 멤버별로 상태 정보 구성
        members_list = []
        overall_problem_counts = {
            "not_attempted_count": 0,
            "in_progress_count": 0,
            "completed_count": 0,
            "total": 0,
        }
        overall_note_counts = {
            "not_completed_count": 0,
            "completed_count": 0,
            "total": 0,
        }

        for member in members:
            member_assignments = []
            member_problem_counts = {
                "not_attempted_count": 0,
                "in_progress_count": 0,
                "completed_count": 0,
            }
            member_note_counts = {"not_completed_count": 0, "completed_count": 0}

            for assignment in assignments:
                status = status_dict.get((assignment.id, member.user_id))
                note = note_dict.get((assignment.problem_id, member.user_id))

                problem_status = (
                    status.status if status else ProblemStatus.NOT_ATTEMPTED
                )
                note_status = "completed" if note else "not_completed"

                member_assignments.append(
                    {
                        "problem_id": assignment.problem_id,
                        "boj_number": assignment.problem.boj_number,
                        "title": assignment.problem.title,
                        "problem_status": problem_status,
                        "note_status": note_status,
                        "last_updated_at": (
                            status.last_updated_at.isoformat() if status else None
                        ),
                    }
                )

                # 멤버별 카운트
                if problem_status == ProblemStatus.NOT_ATTEMPTED:
                    member_problem_counts["not_attempted_count"] += 1
                elif problem_status == ProblemStatus.IN_PROGRESS:
                    member_problem_counts["in_progress_count"] += 1
                elif problem_status == ProblemStatus.COMPLETED:
                    member_problem_counts["completed_count"] += 1

                if note_status == "not_completed":
                    member_note_counts["not_completed_count"] += 1
                else:
                    member_note_counts["completed_count"] += 1

                # 전체 카운트
                overall_problem_counts["total"] += 1
                overall_note_counts["total"] += 1
                if problem_status == ProblemStatus.NOT_ATTEMPTED:
                    overall_problem_counts["not_attempted_count"] += 1
                elif problem_status == ProblemStatus.IN_PROGRESS:
                    overall_problem_counts["in_progress_count"] += 1
                elif problem_status == ProblemStatus.COMPLETED:
                    overall_problem_counts["completed_count"] += 1

                if note_status == "not_completed":
                    overall_note_counts["not_completed_count"] += 1
                else:
                    overall_note_counts["completed_count"] += 1

            members_list.append(
                {
                    "member_id": member.user_id,
                    "member_email": member.user.email,
                    "username": member.user.boj_username,
                    "assignments": member_assignments,
                    "problem_status_summary": member_problem_counts,
                    "note_status_summary": member_note_counts,
                    "total_count": len(member_assignments),
                }
            )

        return {
            "date": target_date.isoformat(),
            "view": "group",
            "members": members_list,
            "total_members": len(members_list),
            "overall_summary": {
                "problem_status_summary": overall_problem_counts,
                "note_status_summary": overall_note_counts,
            },
        }

