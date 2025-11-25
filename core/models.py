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

