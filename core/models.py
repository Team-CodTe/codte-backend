import secrets
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Provider(models.TextChoices):
    """소셜 로그인 제공자"""

    GITHUB = "github", "GitHub"
    GOOGLE = "google", "Google"


class StudyRole(models.TextChoices):
    """스터디 역할"""

    OWNER = "owner", "Owner"
    MEMBER = "member", "Member"


class ProblemStatus(models.TextChoices):
    """문제 풀이 상태"""

    NOT_ATTEMPTED = "not_attempted", "미시도"
    IN_PROGRESS = "in_progress", "진행중"
    COMPLETED = "completed", "완료"


class User(AbstractUser):
    """커스텀 User 모델"""

    email = models.EmailField(unique=True, verbose_name="이메일")
    provider = models.CharField(
        max_length=20, choices=Provider.choices, verbose_name="소셜 로그인 제공자"
    )
    boj_username = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="백준 사용자명"
    )
    profile_img_url = models.URLField(
        max_length=2048, blank=True, null=True, verbose_name="프로필 이미지 URL"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        db_table = "users"
        verbose_name = "사용자"
        verbose_name_plural = "사용자들"

    def __str__(self):
        return f"{self.email} ({self.provider})"


class Study(models.Model):
    """스터디 모델"""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_studies",
        verbose_name="소유자",
    )
    name = models.CharField(max_length=100, verbose_name="스터디명")
    description = models.TextField(blank=True, verbose_name="설명")
    invite_code = models.CharField(
        max_length=8, unique=True, db_index=True, verbose_name="초대 코드"
    )
    daily_problem_count = models.IntegerField(default=3, verbose_name="일일 문제 수")
    tier_min = models.IntegerField(verbose_name="추천 문제 최소 티어")
    tier_max = models.IntegerField(verbose_name="추천 문제 최대 티어")
    min_solved = models.IntegerField(
        blank=True, null=True, verbose_name="추천 문제 최소 푼 사람 수"
    )
    max_solved = models.IntegerField(
        blank=True, null=True, verbose_name="추천 문제 최대 푼 사람 수"
    )
    template_content = models.TextField(
        default="## 접근 방법\n - \n - \n\n## 코드\n```\n여기에 코드를 입력하세요\n```\n\n## 회고\n - \n - \n",
        verbose_name="템플릿 내용",
    )
    last_problem_refreshed_at = models.DateTimeField(
        blank=True, null=True, verbose_name="마지막 문제 갱신 시간"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        db_table = "studies"
        verbose_name = "스터디"
        verbose_name_plural = "스터디들"

    def __str__(self):
        return f"{self.name} (by {self.owner.email})"

    def save(self, *args, **kwargs):
        """invite_code가 없을 경우 자동 생성"""
        if not self.invite_code:
            self.invite_code = self._generate_invite_code()
        super().save(*args, **kwargs)

    def _generate_invite_code(self):
        """고유한 invite_code 생성"""
        while True:
            code = secrets.token_urlsafe(8)[:8].upper()
            if not Study.objects.filter(invite_code=code).exists():
                return code


class StudyMember(models.Model):
    """스터디 멤버 모델"""

    study = models.ForeignKey(
        "Study", on_delete=models.CASCADE, related_name="members", verbose_name="스터디"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_memberships",
        verbose_name="사용자",
    )
    role = models.CharField(
        max_length=10, choices=StudyRole.choices, verbose_name="역할"
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="가입일시")

    class Meta:
        db_table = "study_members"
        unique_together = [("study", "user")]
        verbose_name = "스터디 멤버"
        verbose_name_plural = "스터디 멤버들"

    def __str__(self):
        return f"{self.user.email} - {self.study.name} ({self.role})"


class Problem(models.Model):
    """문제 모델"""

    boj_number = models.IntegerField(
        unique=True, db_index=True, verbose_name="백준 문제 번호"
    )
    title = models.CharField(max_length=200, verbose_name="문제 제목")
    tier = models.IntegerField(verbose_name="티어")
    link = models.URLField(verbose_name="문제 링크")

    class Meta:
        db_table = "problems"
        verbose_name = "문제"
        verbose_name_plural = "문제들"

    def __str__(self):
        return f"{self.boj_number}: {self.title}"


class DailyAssignment(models.Model):
    """일일 과제 모델"""

    study = models.ForeignKey(
        "Study",
        on_delete=models.CASCADE,
        related_name="daily_assignments",
        verbose_name="스터디",
    )
    problem = models.ForeignKey(
        "Problem",
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="문제",
    )
    assigned_date = models.DateField(db_index=True, verbose_name="할당일")
    is_custom = models.BooleanField(default=False, verbose_name="커스텀 문제 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        db_table = "daily_assignments"
        unique_together = [("study", "problem", "assigned_date")]
        ordering = ["-assigned_date"]
        verbose_name = "일일 과제"
        verbose_name_plural = "일일 과제들"

    def __str__(self):
        return f"{self.study.name} - {self.problem.title} ({self.assigned_date})"


class SolutionNote(models.Model):
    """풀이 노트 모델"""

    study = models.ForeignKey(
        "Study",
        on_delete=models.CASCADE,
        related_name="solution_notes",
        verbose_name="스터디",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solution_notes",
        verbose_name="사용자",
    )
    problem = models.ForeignKey(
        "Problem",
        on_delete=models.CASCADE,
        related_name="solution_notes",
        verbose_name="문제",
    )
    assigned_date = models.DateField(blank=True, null=True, verbose_name="문제 배정일")
    content = models.TextField(verbose_name="내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        db_table = "solution_notes"
        unique_together = [("study", "user", "problem")]
        ordering = ["-created_at"]
        verbose_name = "풀이 노트"
        verbose_name_plural = "풀이 노트들"

    def __str__(self):
        return f"{self.user.email} - {self.problem.title} ({self.study.name})"


class ProblemSolvingStatus(models.Model):
    """문제 풀이 상태 모델"""

    assignment = models.ForeignKey(
        "DailyAssignment",
        on_delete=models.CASCADE,
        related_name="solving_statuses",
        verbose_name="일일 과제",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solving_statuses",
        verbose_name="사용자",
    )
    status = models.CharField(
        max_length=20,
        choices=ProblemStatus.choices,
        default=ProblemStatus.NOT_ATTEMPTED,
        verbose_name="풀이 상태",
    )
    last_updated_at = models.DateTimeField(
        auto_now=True, verbose_name="마지막 업데이트 시간"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        db_table = "problem_solving_statuses"
        unique_together = [("assignment", "user")]
        indexes = [
            models.Index(fields=["assignment", "user"]),
            models.Index(fields=["assignment"]),
            models.Index(fields=["user"]),
        ]
        verbose_name = "문제 풀이 상태"
        verbose_name_plural = "문제 풀이 상태들"

    def __str__(self):
        return f"{self.user.email} - {self.assignment.problem.title} ({self.assignment.assigned_date}) - {self.get_status_display()}"


class SolutionNoteReview(models.Model):
    """AI 풀이 노트 리뷰 모델"""

    solution_note = models.OneToOneField(
        "SolutionNote",
        on_delete=models.CASCADE,
        related_name="solution_note_review",
        verbose_name="풀이 노트",
    )
    review_content = models.TextField(verbose_name="리뷰 내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        db_table = "solution_note_reviews"
        verbose_name = "풀이 노트 리뷰"
        verbose_name_plural = "풀이 노트 리뷰들"

    def __str__(self):
        return f"Review for {self.solution_note}"
