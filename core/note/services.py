from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from core.models import SolutionNote, Study, Problem, StudyMember


class SolutionNoteService:
    """풀이 노트 관련 비즈니스 로직 서비스"""

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
        if not StudyMember.objects.filter(study=study, user=user).exists():
            raise ValueError("스터디 멤버만 풀이 노트를 작성할 수 있습니다.")

        # 풀이 노트 생성 (unique_together 제약으로 중복 방지)
        try:
            solution_note = SolutionNote.objects.create(
                study=study,
                user=user,
                problem=problem,
                content=content,
            )
        except IntegrityError:
            raise ValueError("이미 해당 문제에 대한 풀이 노트가 존재합니다.")

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
            raise ValueError("풀이 노트 작성자만 수정할 수 있습니다.")

        # 풀이 노트 수정
        solution_note.content = content
        solution_note.save()

        return solution_note
