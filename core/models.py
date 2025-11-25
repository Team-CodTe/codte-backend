import secrets
from django.contrib.auth.models import AbstractUser
from django.db import models


class Provider(models.TextChoices):
    """소셜 로그인 제공자"""
    GITHUB = 'github', 'GitHub'


class StudyRole(models.TextChoices):
    """스터디 역할"""
    OWNER = 'owner', 'Owner'
    MEMBER = 'member', 'Member'


class User(AbstractUser):
    """커스텀 User 모델"""
    email = models.EmailField(unique=True, verbose_name='이메일')
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        verbose_name='소셜 로그인 제공자'
    )
    boj_username = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='백준 사용자명'
    )
    profile_img_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='프로필 이미지 URL'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일시'
    )

    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'

    def __str__(self):
        return f"{self.email} ({self.provider})"


class Study(models.Model):
    """스터디 모델"""
    owner = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='owned_studies',
        verbose_name='소유자'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='스터디명'
    )
    description = models.TextField(
        blank=True,
        verbose_name='설명'
    )
    invite_code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        verbose_name='초대 코드'
    )
    daily_problem_count = models.IntegerField(
        default=3,
        verbose_name='일일 문제 수'
    )
    target_tier = models.CharField(
        max_length=20,
        verbose_name='목표 티어'
    )
    template_content = models.TextField(
        default="## 접근 방법\n\n## 코드\n\n## 회고",
        verbose_name='템플릿 내용'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일시'
    )

    class Meta:
        db_table = 'studies'
        verbose_name = '스터디'
        verbose_name_plural = '스터디들'

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
