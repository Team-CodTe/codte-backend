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

    def get_problem_members_status(self, study_id: int, problem_id: int) -> dict:
        """특정 문제의 모든 멤버 풀이 상태 조회

        Args:
            study_id: 스터디 ID
            problem_id: 문제 ID (Problem 모델의 ID)

        Returns:
            dict: 문제 정보 및 모든 멤버의 풀이 상태
        """
        # 스터디 및 문제 조회
        study = Study.objects.get(id=study_id)
        from core.models import Problem

        problem = Problem.objects.get(id=problem_id)

        # 스터디 멤버 조회
        members = StudyMember.objects.filter(study=study).select_related("user")

        # 해당 문제가 포함된 모든 DailyAssignment 조회 (날짜 무관)
        assignments = DailyAssignment.objects.filter(
            study=study, problem=problem
        ).select_related("problem")

        if not assignments.exists():
            return {
                "problem_id": problem_id,
                "boj_number": problem.boj_number,
                "title": problem.title,
                "members_status": [],
                "problem_status_summary": {
                    "not_attempted_count": 0,
                    "in_progress_count": 0,
                    "completed_count": 0,
                    "total_members": len(members),
                },
                "note_status_summary": {
                    "not_completed_count": 0,
                    "completed_count": 0,
                    "total_members": len(members),
                },
            }

        # 모든 assignment에 대한 ProblemSolvingStatus 조회
        # 가장 최근 assignment의 상태를 사용 (또는 모든 assignment의 상태를 집계)
        # 일단 가장 최근 assignment만 사용
        latest_assignment = assignments.order_by("-assigned_date").first()

        statuses = ProblemSolvingStatus.objects.filter(
            assignment=latest_assignment
        ).select_related("user")

        # status를 user_id로 매핑
        status_dict = {status.user_id: status for status in statuses}

        # 모든 멤버의 SolutionNote 조회
        solution_notes = SolutionNote.objects.filter(
            study=study, problem=problem
        ).select_related("user")

        # note를 user_id로 매핑
        note_dict = {note.user_id: note for note in solution_notes}

        # 멤버별 상태 정보 구성
        members_status_list = []
        problem_status_counts = {
            "not_attempted_count": 0,
            "in_progress_count": 0,
            "completed_count": 0,
            "total_members": len(members),
        }
        note_status_counts = {
            "not_completed_count": 0,
            "completed_count": 0,
            "total_members": len(members),
        }

        for member in members:
            status = status_dict.get(member.user_id)
            note = note_dict.get(member.user_id)

            problem_status = (
                status.status if status else ProblemStatus.NOT_ATTEMPTED
            )
            note_status = "completed" if note else "not_completed"

            members_status_list.append(
                {
                    "member_id": member.user_id,
                    "member_email": member.user.email,
                    "username": member.user.boj_username,
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
            "problem_id": problem_id,
            "boj_number": problem.boj_number,
            "title": problem.title,
            "members_status": members_status_list,
            "problem_status_summary": problem_status_counts,
            "note_status_summary": note_status_counts,
        }

    def get_statistics(
        self,
        user,
        study_id: int,
        view: str = "me",
        member_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """문제 풀이 통계 조회

        Args:
            user: 조회하는 사용자
            study_id: 스터디 ID
            view: 조회 방식 ('me', 'group', 'member', 기본값: 'me')
            member_id: 멤버 ID (view='member'일 때 필수)
            start_date: 시작 날짜 (선택)
            end_date: 종료 날짜 (선택)

        Returns:
            dict: 통계 정보 (view에 따라 구조가 다름)
        """
        # 스터디 조회
        study = Study.objects.get(id=study_id)

        if view == "me":
            return self._get_my_statistics(user, study, start_date, end_date)
        elif view == "group":
            return self._get_group_statistics(study, start_date, end_date)
        elif view == "member":
            if member_id is None:
                raise ValueError("view='member'일 때 member_id가 필요합니다.")
            return self._get_member_statistics(study, member_id, start_date, end_date)
        else:
            raise ValueError(f"잘못된 view 값입니다: {view}")

    def _get_my_statistics(
        self, user, study, start_date: Optional[date], end_date: Optional[date]
    ) -> dict:
        """현재 사용자의 통계 조회"""
        # 날짜 범위 필터링
        assignments_query = DailyAssignment.objects.filter(study=study)
        if start_date:
            assignments_query = assignments_query.filter(
                assigned_date__gte=start_date
            )
        if end_date:
            assignments_query = assignments_query.filter(assigned_date__lte=end_date)

        assignments = assignments_query.select_related("problem")

        # 사용자의 ProblemSolvingStatus 조회
        statuses = ProblemSolvingStatus.objects.filter(
            assignment__in=assignments, user=user
        ).select_related("assignment", "assignment__problem")

        # 사용자의 SolutionNote 조회
        problems = [a.problem for a in assignments]
        solution_notes = SolutionNote.objects.filter(
            study=study, user=user, problem__in=problems
        ).select_related("problem")

        # status와 note를 매핑
        status_dict = {status.assignment_id: status for status in statuses}
        note_dict = {note.problem_id: note for note in solution_notes}

        # 전체 통계 계산
        total_assigned = len(assignments)
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

        # 완료율 계산
        completed_count = problem_status_counts["completed_count"]
        problem_completion_rate = (
            completed_count / total_assigned if total_assigned > 0 else 0.0
        )
        note_completed_count = note_status_counts["completed_count"]
        note_completion_rate = (
            note_completed_count / total_assigned if total_assigned > 0 else 0.0
        )

        # 일별 통계 계산
        daily_statistics = self._calculate_daily_statistics(
            user, study, assignments, status_dict, note_dict, start_date, end_date
        )

        return {
            "view": "me",
            "member_id": user.id,
            "member_email": user.email,
            "username": user.boj_username,
            "total_assigned": total_assigned,
            "problem_status_summary": problem_status_counts,
            "note_status_summary": note_status_counts,
            "problem_completion_rate": problem_completion_rate,
            "note_completion_rate": note_completion_rate,
            "date_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "daily_statistics": daily_statistics,
        }

    def _get_group_statistics(
        self, study, start_date: Optional[date], end_date: Optional[date]
    ) -> dict:
        """모든 멤버의 통계 조회 (그룹 통계)"""
        # 날짜 범위 필터링
        assignments_query = DailyAssignment.objects.filter(study=study)
        if start_date:
            assignments_query = assignments_query.filter(
                assigned_date__gte=start_date
            )
        if end_date:
            assignments_query = assignments_query.filter(assigned_date__lte=end_date)

        assignments = assignments_query.select_related("problem")

        # 스터디 멤버 조회
        members = StudyMember.objects.filter(study=study).select_related("user")

        # 모든 멤버의 ProblemSolvingStatus 조회
        statuses = ProblemSolvingStatus.objects.filter(
            assignment__in=assignments
        ).select_related("assignment", "assignment__problem", "user")

        # 모든 멤버의 SolutionNote 조회
        problems = [a.problem for a in assignments]
        solution_notes = SolutionNote.objects.filter(
            study=study, problem__in=problems
        ).select_related("problem", "user")

        # status와 note를 매핑
        status_dict = {
            (status.assignment_id, status.user_id): status for status in statuses
        }
        note_dict = {(note.problem_id, note.user_id): note for note in solution_notes}

        # 전체 통계 계산
        total_assigned = len(assignments) * len(members)
        overall_problem_counts = {
            "not_attempted_count": 0,
            "in_progress_count": 0,
            "completed_count": 0,
        }
        overall_note_counts = {"not_completed_count": 0, "completed_count": 0}

        # 멤버별 통계 계산
        members_statistics = []
        completion_rates = []

        for member in members:
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

            # 멤버별 완료율 계산
            member_total = len(assignments)
            member_problem_rate = (
                member_problem_counts["completed_count"] / member_total
                if member_total > 0
                else 0.0
            )
            member_note_rate = (
                member_note_counts["completed_count"] / member_total
                if member_total > 0
                else 0.0
            )
            completion_rates.append(member_problem_rate)

            members_statistics.append(
                {
                    "member_id": member.user_id,
                    "member_email": member.user.email,
                    "username": member.user.boj_username,
                    "total_assigned": member_total,
                    "problem_status_summary": member_problem_counts,
                    "note_status_summary": member_note_counts,
                    "problem_completion_rate": member_problem_rate,
                    "note_completion_rate": member_note_rate,
                }
            )

        # 평균 완료율 계산
        average_problem_rate = (
            sum(completion_rates) / len(completion_rates)
            if completion_rates
            else 0.0
        )
        average_note_rate = (
            sum(
                [
                    m["note_completion_rate"]
                    for m in members_statistics
                    if m["total_assigned"] > 0
                ]
            )
            / len([m for m in members_statistics if m["total_assigned"] > 0])
            if members_statistics
            else 0.0
        )

        # 일별 통계 계산
        daily_statistics = self._calculate_group_daily_statistics(
            study, members, assignments, status_dict, note_dict, start_date, end_date
        )

        return {
            "view": "group",
            "total_members": len(members),
            "total_assigned": total_assigned,
            "problem_status_summary": overall_problem_counts,
            "note_status_summary": overall_note_counts,
            "average_problem_completion_rate": average_problem_rate,
            "average_note_completion_rate": average_note_rate,
            "date_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "members_statistics": members_statistics,
            "daily_statistics": daily_statistics,
        }

    def _get_member_statistics(
        self, study, member_id: int, start_date: Optional[date], end_date: Optional[date]
    ) -> dict:
        """특정 멤버의 통계 조회"""
        from core.models import User

        member = User.objects.get(id=member_id)

        # 날짜 범위 필터링
        assignments_query = DailyAssignment.objects.filter(study=study)
        if start_date:
            assignments_query = assignments_query.filter(
                assigned_date__gte=start_date
            )
        if end_date:
            assignments_query = assignments_query.filter(assigned_date__lte=end_date)

        assignments = assignments_query.select_related("problem")

        # 멤버의 ProblemSolvingStatus 조회
        statuses = ProblemSolvingStatus.objects.filter(
            assignment__in=assignments, user=member
        ).select_related("assignment", "assignment__problem")

        # 멤버의 SolutionNote 조회
        problems = [a.problem for a in assignments]
        solution_notes = SolutionNote.objects.filter(
            study=study, user=member, problem__in=problems
        ).select_related("problem")

        # status와 note를 매핑
        status_dict = {status.assignment_id: status for status in statuses}
        note_dict = {note.problem_id: note for note in solution_notes}

        # 전체 통계 계산
        total_assigned = len(assignments)
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

        # 완료율 계산
        completed_count = problem_status_counts["completed_count"]
        problem_completion_rate = (
            completed_count / total_assigned if total_assigned > 0 else 0.0
        )
        note_completed_count = note_status_counts["completed_count"]
        note_completion_rate = (
            note_completed_count / total_assigned if total_assigned > 0 else 0.0
        )

        # 일별 통계 계산
        daily_statistics = self._calculate_daily_statistics(
            member, study, assignments, status_dict, note_dict, start_date, end_date
        )

        return {
            "view": "member",
            "member_id": member.id,
            "member_email": member.email,
            "username": member.boj_username,
            "total_assigned": total_assigned,
            "problem_status_summary": problem_status_counts,
            "note_status_summary": note_status_counts,
            "problem_completion_rate": problem_completion_rate,
            "note_completion_rate": note_completion_rate,
            "date_range": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "daily_statistics": daily_statistics,
        }

    def _calculate_daily_statistics(
        self,
        user,
        study,
        assignments,
        status_dict,
        note_dict,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[dict]:
        """일별 통계 계산 (개인용)"""
        from collections import defaultdict

        # 날짜별로 그룹화
        daily_data = defaultdict(
            lambda: {
                "assignments": [],
                "problem_counts": {
                    "not_attempted_count": 0,
                    "in_progress_count": 0,
                    "completed_count": 0,
                },
                "note_counts": {"not_completed_count": 0, "completed_count": 0},
            }
        )

        for assignment in assignments:
            assigned_date = assignment.assigned_date
            daily_data[assigned_date]["assignments"].append(assignment)

        # 각 날짜별 통계 계산
        daily_statistics = []
        for assigned_date in sorted(daily_data.keys()):
            date_assignments = daily_data[assigned_date]["assignments"]
            problem_counts = {
                "not_attempted_count": 0,
                "in_progress_count": 0,
                "completed_count": 0,
            }
            note_counts = {"not_completed_count": 0, "completed_count": 0}

            for assignment in date_assignments:
                status = status_dict.get(assignment.id)
                note = note_dict.get(assignment.problem_id)

                problem_status = (
                    status.status if status else ProblemStatus.NOT_ATTEMPTED
                )
                note_status = "completed" if note else "not_completed"

                if problem_status == ProblemStatus.NOT_ATTEMPTED:
                    problem_counts["not_attempted_count"] += 1
                elif problem_status == ProblemStatus.IN_PROGRESS:
                    problem_counts["in_progress_count"] += 1
                elif problem_status == ProblemStatus.COMPLETED:
                    problem_counts["completed_count"] += 1

                if note_status == "not_completed":
                    note_counts["not_completed_count"] += 1
                else:
                    note_counts["completed_count"] += 1

            daily_statistics.append(
                {
                    "date": assigned_date.isoformat(),
                    "assigned_count": len(date_assignments),
                    "problem_status_summary": problem_counts,
                    "note_status_summary": note_counts,
                }
            )

        return daily_statistics

    def _calculate_group_daily_statistics(
        self,
        study,
        members,
        assignments,
        status_dict,
        note_dict,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> List[dict]:
        """일별 통계 계산 (그룹용)"""
        from collections import defaultdict

        # 날짜별로 그룹화
        daily_data = defaultdict(lambda: {"assignments": []})

        for assignment in assignments:
            assigned_date = assignment.assigned_date
            daily_data[assigned_date]["assignments"].append(assignment)

        # 각 날짜별 통계 계산
        daily_statistics = []
        for assigned_date in sorted(daily_data.keys()):
            date_assignments = daily_data[assigned_date]["assignments"]
            problem_counts = {
                "not_attempted_count": 0,
                "in_progress_count": 0,
                "completed_count": 0,
            }
            note_counts = {"not_completed_count": 0, "completed_count": 0}

            for assignment in date_assignments:
                for member in members:
                    status = status_dict.get((assignment.id, member.user_id))
                    note = note_dict.get((assignment.problem_id, member.user_id))

                    problem_status = (
                        status.status if status else ProblemStatus.NOT_ATTEMPTED
                    )
                    note_status = "completed" if note else "not_completed"

                    if problem_status == ProblemStatus.NOT_ATTEMPTED:
                        problem_counts["not_attempted_count"] += 1
                    elif problem_status == ProblemStatus.IN_PROGRESS:
                        problem_counts["in_progress_count"] += 1
                    elif problem_status == ProblemStatus.COMPLETED:
                        problem_counts["completed_count"] += 1

                    if note_status == "not_completed":
                        note_counts["not_completed_count"] += 1
                    else:
                        note_counts["completed_count"] += 1

            daily_statistics.append(
                {
                    "date": assigned_date.isoformat(),
                    "assigned_count": len(date_assignments),
                    "problem_status_summary": problem_counts,
                    "note_status_summary": note_counts,
                }
            )

        return daily_statistics

