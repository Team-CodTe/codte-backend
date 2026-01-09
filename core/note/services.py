from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.db.models import Q

from core.models import SolutionNote, Study, Problem, StudyMember, DailyAssignment


class SolutionNoteService:
    """풀이 노트 관련 비즈니스 로직 서비스"""

    def _check_study_membership(self, user, study, error_message):
        """
        스터디 멤버 여부를 확인하고, 멤버가 아닐 경우 ValueError를 발생시킵니다.

        Args:
            user: 확인할 사용자 (User 인스턴스)
            study: 확인할 스터디 (Study 인스턴스)
            error_message: 멤버가 아닐 경우 발생시킬 에러 메시지 (str)

        Raises:
            ValueError: 스터디 멤버가 아닌 경우
        """
        if not StudyMember.objects.filter(study=study, user=user).exists():
            raise ValueError(error_message)

    def create_solution_note(self, user, study_id, problem_id, content):
        """
        풀이 노트를 생성합니다.

        Args:
            user: 노트를 작성하는 사용자 (User 인스턴스)
            study_id: 스터디 ID (int)
            problem_id: 문제 ID (int)
            content: 풀이 본문 (str)

        Returns:
            SolutionNote: 생성된 풀이 노트 인스턴스

        Raises:
            Http404: 스터디 또는 문제가 없는 경우
            ValueError: 스터디 멤버가 아니거나, 이미 해당 문제에 대한 노트가 존재하는 경우
        """
        # 스터디와 문제 조회
        study = get_object_or_404(Study, id=study_id)
        problem = get_object_or_404(Problem, id=problem_id)

        # TODO: DailyAssignment에 있는 문제인지 확인하는 로직 추가

        # 스터디 멤버인지 확인
        self._check_study_membership(
            user, study, "스터디 멤버만 풀이 노트를 작성할 수 있습니다."
        )

        # DailyAssignment에서 assigned_date 조회
        assignment = DailyAssignment.objects.filter(
            study=study, problem=problem
        ).first()
        assigned_date = assignment.assigned_date if assignment else None

        # 풀이 노트 생성 (unique_together 제약으로 중복 방지)
        try:
            solution_note = SolutionNote.objects.create(
                study=study,
                user=user,
                problem=problem,
                content=content,
                assigned_date=assigned_date,
            )
        except IntegrityError:
            raise ValueError("이미 풀이 글을 작성한 문제입니다.")

        return solution_note

    def update_solution_note(self, user, note_id, content):
        """
        풀이 노트를 수정합니다.

        Args:
            user: 노트를 수정하는 사용자 (User 인스턴스)
            note_id: 풀이 노트 ID (int)
            content: 수정할 풀이 본문 (str)

        Returns:
            SolutionNote: 수정된 풀이 노트 인스턴스

        Raises:
            Http404: 풀이 노트가 없는 경우
            ValueError: 노트 작성자가 아닌 경우
        """
        # 풀이 노트 조회
        solution_note = get_object_or_404(SolutionNote, id=note_id)

        # 작성자만 수정 가능
        if solution_note.user != user:
            raise ValueError("풀이 글 작성자만 수정할 수 있습니다.")

        # 풀이 노트 수정
        solution_note.content = content
        solution_note.save()

        return solution_note

    def delete_solution_note(self, user, note_id):
        """
        풀이 노트를 삭제합니다.

        Args:
            user: 노트를 삭제하는 사용자 (User 인스턴스)
            note_id: 풀이 노트 ID (int)

        Raises:
            Http404: 풀이 노트가 없는 경우
            ValueError: 노트 작성자가 아닌 경우
        """
        # 풀이 노트 조회
        solution_note = get_object_or_404(SolutionNote, id=note_id)

        # 작성자만 삭제 가능
        if solution_note.user != user:
            raise ValueError("풀이 글 작성자만 삭제할 수 있습니다.")

        # 풀이 노트 삭제
        solution_note.delete()

    def get_solution_notes(
        self,
        user,
        study_id,
        problem_id=None,
        assigned_date=None,
        created_date=None,
        query=None,
    ):
        """
        스터디원들의 풀이 노트 목록을 조회합니다.

        Args:
            user: 조회하는 사용자 (User 인스턴스)
            study_id: 스터디 ID (int)
            problem_id: 문제 ID (int, 선택)
            assigned_date: 문제 추천 날짜 (date, 선택)
            created_date: 작성일 (date, 선택)
            query: 통합 검색 (제목, 문제 번호, 작성자)

        Returns:
            QuerySet: 풀이 노트 QuerySet

        Raises:
            Http404: 스터디 또는 문제가 없는 경우
            ValueError: 스터디 멤버가 아닌 경우
        """
        # 스터디 조회
        study = get_object_or_404(Study, id=study_id)

        # 스터디 멤버인지 확인
        self._check_study_membership(
            user, study, "스터디 멤버만 풀이 글을 조회할 수 있습니다."
        )

        # 풀이 노트 목록 조회 (problem_id가 있으면 필터링)
        solution_notes = SolutionNote.objects.filter(study=study)

        if problem_id is not None:
            problem = get_object_or_404(Problem, id=problem_id)
            solution_notes = solution_notes.filter(problem=problem)

        # 검색 필터 적용
        if assigned_date is not None:
            solution_notes = solution_notes.filter(assigned_date=assigned_date)

        if created_date is not None:
            solution_notes = solution_notes.filter(created_at__date=created_date)

        if query:
            q_filter = Q(problem__title__icontains=query) | Q(
                user__username__icontains=query
            )
            if query.isdigit():
                try:
                    q_filter |= Q(problem__boj_number=int(query))
                except ValueError:
                    # 숫자가 너무 커서 변환할 수 없는 경우 등 예외 처리
                    pass
            solution_notes = solution_notes.filter(q_filter)

        solution_notes = solution_notes.select_related(
            "user", "study", "problem"
        ).order_by("-created_at")

        return solution_notes

    def get_solution_note(self, user, note_id):
        """
        특정 풀이 노트를 조회합니다.

        Args:
            user: 조회하는 사용자 (User 인스턴스)
            note_id: 풀이 노트 ID (int)

        Returns:
            SolutionNote: 풀이 노트 인스턴스

        Raises:
            Http404: 풀이 노트가 없는 경우
            ValueError: 스터디 멤버가 아닌 경우
        """
        # 풀이 노트 조회
        solution_note = get_object_or_404(
            SolutionNote.objects.select_related("user", "study", "problem"),
            id=note_id,
        )

        # 스터디 멤버인지 확인
        self._check_study_membership(
            user, solution_note.study, "스터디 멤버만 풀이 글을 조회할 수 있습니다."
        )

        return solution_note

    def get_study_template_content(self, user, study_id):
        """
        스터디의 템플릿 내용을 조회합니다.

        Args:
            user: 조회하는 사용자 (User 인스턴스)
            study_id: 스터디 ID (int)

        Returns:
            Study: 스터디 인스턴스

        Raises:
            Http404: 스터디가 없는 경우
            ValueError: 스터디 멤버가 아닌 경우
        """
        # 스터디 조회
        study = get_object_or_404(Study, id=study_id)

        # 스터디 멤버인지 확인
        self._check_study_membership(
            user, study, "스터디 멤버만 템플릿 내용을 조회할 수 있습니다."
        )

        return study
