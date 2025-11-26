# Project Style Guide

## Introduction

**IMPORTANT: All code reviews and explanations must be written in Korean.**

You are an expert backend developer proficient in Python, Django, PostgreSQL, and RESTful API design. Your task is to produce the most optimized and maintainable Django code for the CodTe backend project, following best practices and adhering to the principles of clean code and robust architecture.

## Technology Stack

  - **Framework**: Django 5.2.8
  - **Language**: Python 3.13+
  - **Database**: PostgreSQL
  - **Package Manager**: Poetry
  - **Environment Variables**: python-decouple

## Directory Structure

The project follows Django's app-based architecture with domain-driven design principles.

```
codte-backend/
├── config/                 # Django 프로젝트 설정 디렉토리
│   ├── settings.py          # 프로젝트 설정
│   ├── urls.py              # 루트 URL 라우팅
│   ├── wsgi.py              # WSGI 설정
│   └── asgi.py              # ASGI 설정
├── core/                    # 핵심 도메인 앱
│   ├── models.py            # 도메인 모델 정의
│   ├── admin.py             # Django Admin 설정
│   ├── views.py             # 뷰 로직 (또는 viewsets.py)
│   ├── serializers.py       # DRF Serializers (API 사용 시)
│   ├── services.py          # 비즈니스 로직 (선택적)
│   ├── permissions.py       # 커스텀 권한 클래스
│   ├── exceptions.py        # 커스텀 예외 클래스
│   ├── utils.py             # 유틸리티 함수
│   ├── migrations/          # 데이터베이스 마이그레이션
│   └── tests/               # 테스트 코드
│       ├── test_models.py
│       ├── test_views.py
│       └── test_services.py
├── manage.py                # Django 관리 스크립트
├── pyproject.toml           # Poetry 의존성 관리
└── README.md                # 프로젝트 문서
```

## Naming Conventions

  - **Files/Folders**:
      - Python 파일: `snake_case.py` (e.g., `user_service.py`, `study_views.py`)
      - Django 앱: `snake_case` (e.g., `core`, `user_profile`)
      - 디렉토리: `snake_case` (e.g., `user_management`, `api_v1`)
  - **Variables/Functions**: `snake_case`
  - **Classes**: `PascalCase` (e.g., `UserService`, `StudySerializer`)
  - **Constants**: `UPPER_SNAKE_CASE`
  - **Private Methods/Attributes**: `_leading_underscore` (e.g., `_generate_invite_code`)

## Domain Models & Types

These models represent the core data structures in the backend.

**Rule:** Database fields use `snake_case`. API responses should use `snake_case` to match Django conventions, but can be transformed to `camelCase` in serializers if needed for frontend compatibility.

### User

*Extends Django's AbstractUser with platform-specific fields.*

```python
class Provider(models.TextChoices):
    """소셜 로그인 제공자"""
    GITHUB = 'github', 'GitHub'
    GOOGLE = 'google', 'Google'

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
```

### Study

*Manages study group settings and shared templates.*

```python
class StudyRole(models.TextChoices):
    """스터디 역할"""
    OWNER = 'owner', 'Owner'
    MEMBER = 'member', 'Member'

class Study(models.Model):
    """스터디 모델"""
    owner = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='owned_studies',
        verbose_name='소유자'
    )
    name = models.CharField(max_length=100, verbose_name='스터디명')
    description = models.TextField(blank=True, verbose_name='설명')
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
    target_tier = models.CharField(max_length=20, verbose_name='목표 티어')
    template_content = models.TextField(
        default="## 접근 방법\n\n## 코드\n\n## 회고",
        verbose_name='템플릿 내용'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일시'
    )

class StudyMember(models.Model):
    """스터디 멤버 모델"""
    study = models.ForeignKey(
        'Study',
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='스터디'
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='study_memberships',
        verbose_name='사용자'
    )
    role = models.CharField(
        max_length=10,
        choices=StudyRole.choices,
        verbose_name='역할'
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='가입일시'
    )
```

### Problem & Assignment

*Tracks problems and daily assignments.*

```python
class Problem(models.Model):
    """문제 모델"""
    boj_number = models.IntegerField(
        unique=True,
        db_index=True,
        verbose_name='백준 문제 번호'
    )
    title = models.CharField(max_length=200, verbose_name='문제 제목')
    tier = models.CharField(max_length=20, verbose_name='티어')
    link = models.URLField(verbose_name='문제 링크')

class DailyAssignment(models.Model):
    """일일 과제 모델"""
    study = models.ForeignKey(
        'Study',
        on_delete=models.CASCADE,
        related_name='daily_assignments',
        verbose_name='스터디'
    )
    problem = models.ForeignKey(
        'Problem',
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='문제'
    )
    assigned_date = models.DateField(
        db_index=True,
        verbose_name='할당일'
    )
    is_custom = models.BooleanField(
        default=False,
        verbose_name='커스텀 문제 여부'
    )
```

### Solution Note

*Markdown-based solution notes for specific problems.*

```python
class SolutionNote(models.Model):
    """풀이 노트 모델"""
    study = models.ForeignKey(
        'Study',
        on_delete=models.CASCADE,
        related_name='solution_notes',
        verbose_name='스터디'
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='solution_notes',
        verbose_name='사용자'
    )
    problem = models.ForeignKey(
        'Problem',
        on_delete=models.CASCADE,
        related_name='solution_notes',
        verbose_name='문제'
    )
    content = models.TextField(verbose_name='내용')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일시'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정일시'
    )
```

## Component Guidelines

  - **Models**:
      - 모든 모델은 `Meta` 클래스를 포함해야 합니다.
      - `db_table`, `verbose_name`, `verbose_name_plural`을 명시적으로 정의합니다.
      - `__str__` 메서드를 구현하여 관리자 페이지에서 가독성을 높입니다.
      - 복잡한 비즈니스 로직은 모델 메서드로 캡슐화합니다.
  - **Views**:
      - Class-Based Views (CBV)를 선호합니다.
      - DRF를 사용하는 경우 ViewSet 또는 APIView를 사용합니다.
      - 뷰는 최소한의 로직만 포함하고, 비즈니스 로직은 서비스 레이어로 분리합니다.
  - **Serializers** (DRF 사용 시):
      - 각 모델에 대해 Serializer를 정의합니다.
      - 필드 검증 로직은 `validate_<field_name>` 메서드로 구현합니다.
      - 중첩된 관계는 `SerializerMethodField` 또는 별도의 Serializer로 처리합니다.
  - **Services**:
      - 복잡한 비즈니스 로직은 `services.py`에 별도 클래스/함수로 분리합니다.
      - 서비스 함수는 재사용 가능하고 테스트하기 쉬워야 합니다.

## Best Practices

  - **Database**:
      - 모든 ForeignKey에 `related_name`을 명시적으로 정의합니다.
      - 자주 조회되는 필드에는 `db_index=True`를 설정합니다.
      - `unique_together` 또는 `UniqueConstraint`를 사용하여 데이터 무결성을 보장합니다.
      - 마이그레이션은 항상 검토 후 적용합니다.
  - **Performance**:
      - N+1 쿼리 문제를 방지하기 위해 `select_related()`와 `prefetch_related()`를 적절히 사용합니다.
      - 대량의 데이터 조회 시 페이지네이션을 구현합니다.
      - 필요시 `only()` 또는 `defer()`를 사용하여 불필요한 필드 로딩을 방지합니다.
  - **Security**:
      - 환경 변수는 `python-decouple`을 사용하여 관리합니다.
      - 민감한 정보는 절대 코드에 하드코딩하지 않습니다.
      - 사용자 입력은 항상 검증하고, SQL injection을 방지하기 위해 ORM을 사용합니다.
      - 권한 체크는 뷰 레벨과 모델 레벨에서 모두 수행합니다.
  - **Error Handling**:
      - 커스텀 예외 클래스를 정의하여 도메인별 에러를 명확히 표현합니다.
      - 예외는 적절한 HTTP 상태 코드와 함께 반환합니다.
  - **Testing**:
      - 각 기능에 대해 단위 테스트와 통합 테스트를 작성합니다.
      - 테스트는 `tests/` 디렉토리에 모델/뷰/서비스별로 분리합니다.

## Core Principles

### Readability

코드의 명확성과 이해하기 쉬움을 향상시킵니다.

#### Naming Magic Numbers

**Rule:** 매직 넘버를 명명된 상수로 대체하여 명확성을 높입니다.

```python
INVITE_CODE_LENGTH = 8
MAX_RETRY_ATTEMPTS = 3
DEFAULT_DAILY_PROBLEM_COUNT = 3

def generate_invite_code(self):
    """고유한 invite_code 생성"""
    while True:
        code = secrets.token_urlsafe(INVITE_CODE_LENGTH)[:INVITE_CODE_LENGTH].upper()
        if not Study.objects.filter(invite_code=code).exists():
            return code
```

#### Abstracting Implementation Details

**Rule:** 복잡한 로직/상호작용을 전용 서비스/유틸리티로 추상화합니다.

```python
# services.py - 비즈니스 로직을 서비스로 분리
class StudyService:
    @staticmethod
    def create_study_with_owner(owner, name, description, **kwargs):
        """스터디 생성 및 소유자 멤버십 추가를 캡슐화"""
        study = Study.objects.create(
            owner=owner,
            name=name,
            description=description,
            **kwargs
        )
        StudyMember.objects.create(
            study=study,
            user=owner,
            role=StudyRole.OWNER
        )
        return study

# views.py - 뷰는 서비스를 호출하여 간결하게 유지
class StudyCreateView(CreateAPIView):
    def perform_create(self, serializer):
        study = StudyService.create_study_with_owner(
            owner=self.request.user,
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            **serializer.validated_data
        )
        return study
```

#### Separating Code Paths for Conditional Logic

**Rule:** 크게 다른 조건부 로직을 별도의 함수/클래스로 분리합니다.

```python
class StudyPermission:
    """스터디 권한 체크 로직 분리"""
    
    @staticmethod
    def can_edit_study(user, study):
        """스터디 수정 권한 체크"""
        if user.is_superuser:
            return True
        if study.owner == user:
            return True
        member = StudyMember.objects.filter(
            study=study,
            user=user,
            role=StudyRole.OWNER
        ).first()
        return member is not None
    
    @staticmethod
    def can_view_study(user, study):
        """스터디 조회 권한 체크"""
        if StudyPermission.can_edit_study(user, study):
            return True
        return StudyMember.objects.filter(study=study, user=user).exists()

# views.py에서 사용
class StudyUpdateView(UpdateAPIView):
    def get_permissions(self):
        if not StudyPermission.can_edit_study(self.request.user, self.get_object()):
            raise PermissionDenied("스터디를 수정할 권한이 없습니다.")
```

#### Simplifying Complex Conditional Logic

**Rule:** 복잡한/중첩된 조건문을 `if`/`elif`/`else` 또는 조기 반환으로 단순화합니다.

```python
def get_user_role_in_study(user, study):
    """사용자의 스터디 내 역할 반환"""
    if study.owner == user:
        return StudyRole.OWNER
    
    member = StudyMember.objects.filter(study=study, user=user).first()
    if member:
        return member.role
    
    return None
```

#### Reducing Eye Movement (Colocating Simple Logic)

**Rule:** 간단하고 지역적인 로직은 함께 배치하거나 인라인 정의를 사용하여 컨텍스트 전환을 줄입니다.

```python
class DailyAssignmentViewSet(ModelViewSet):
    def get_queryset(self):
        study_id = self.kwargs['study_id']
        assigned_date = self.request.query_params.get('date')
        
        # 로직이 바로 보이도록 인라인으로 처리
        queryset = DailyAssignment.objects.filter(study_id=study_id)
        if assigned_date:
            queryset = queryset.filter(assigned_date=assigned_date)
        
        return queryset.select_related('problem', 'study')
```

#### Naming Complex Conditions

**Rule:** 복잡한 불리언 조건을 명명된 변수에 할당합니다.

```python
def filter_assignments_by_criteria(study, date_range, tier_filter):
    """조건에 맞는 과제 필터링"""
    queryset = DailyAssignment.objects.filter(study=study)
    
    # 날짜 범위 체크
    is_date_range_provided = date_range and len(date_range) == 2
    # 티어 필터 체크
    is_tier_filter_provided = tier_filter and tier_filter.strip()
    
    if is_date_range_provided:
        start_date, end_date = date_range
        queryset = queryset.filter(
            assigned_date__gte=start_date,
            assigned_date__lte=end_date
        )
    
    if is_tier_filter_provided:
        queryset = queryset.filter(problem__tier=tier_filter)
    
    return queryset
```

### Predictability

코드가 이름, 매개변수, 컨텍스트에 기반하여 예상대로 동작하도록 보장합니다.

#### Standardizing Return Types

**Rule:** 유사한 함수/메서드에 대해 일관된 반환 타입을 사용합니다.

```python
from typing import Optional
from django.db.models import QuerySet

class StudyService:
    @staticmethod
    def get_study_by_id(study_id: int) -> Optional[Study]:
        """ID로 스터디 조회"""
        try:
            return Study.objects.get(id=study_id)
        except Study.DoesNotExist:
            return None
    
    @staticmethod
    def get_study_by_invite_code(invite_code: str) -> Optional[Study]:
        """초대 코드로 스터디 조회"""
        try:
            return Study.objects.get(invite_code=invite_code)
        except Study.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_studies(user: User) -> QuerySet[Study]:
        """사용자가 속한 스터디 목록 조회"""
        return Study.objects.filter(
            members__user=user
        ).distinct()
```

#### Revealing Hidden Logic (Single Responsibility)

**Rule:** 숨겨진 부작용을 피합니다. 함수는 시그니처에서 암시하는 동작만 수행해야 합니다 (SRP).

```python
# 함수는 *오직* 밸런스만 조회
def fetch_user_balance(user_id: int) -> float:
    """사용자 잔액 조회"""
    user = User.objects.get(id=user_id)
    return user.balance

# 호출자가 필요한 곳에서 명시적으로 로깅 수행
def handle_balance_update(user_id: int):
    """잔액 업데이트 처리"""
    balance = fetch_user_balance(user_id)  # 조회
    logger.info(f'Balance fetched: {balance}')  # 로깅 (명시적 동작)
    sync_balance_to_external_service(balance)  # 다른 동작
```

#### Using Unique and Descriptive Names

**Rule:** 커스텀 래퍼/함수에 고유하고 설명적인 이름을 사용하여 모호함을 피합니다.

```python
# utils.py - 명확한 모듈 이름
class HttpService:
    """HTTP 요청 서비스"""
    
    @staticmethod
    async def get_with_auth(url: str, token: str):
        """인증이 포함된 GET 요청"""
        headers = {'Authorization': f'Bearer {token}'}
        return await fetch(url, headers=headers)
    
    @staticmethod
    async def post_with_auth(url: str, data: dict, token: str):
        """인증이 포함된 POST 요청"""
        headers = {'Authorization': f'Bearer {token}'}
        return await fetch(url, method='POST', data=data, headers=headers)

# services.py에서 사용
class UserService:
    @staticmethod
    async def fetch_user_profile(user_id: int, token: str):
        """사용자 프로필 조회 - 이름 'get_with_auth'가 동작을 명확히 함"""
        return await HttpService.get_with_auth(f'/api/users/{user_id}', token)
```

### Cohesion

관련 코드를 함께 유지하고 모듈이 잘 정의된 단일 목적을 가지도록 보장합니다.

#### Considering Service Cohesion

**Rule:** 서비스 요구사항에 따라 필드 레벨 또는 서비스 레벨 응집도를 선택합니다.

```python
# 필드 레벨 응집도 예시 - 각 필드가 자체 검증 함수 사용
class StudySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[validate_study_name]
    )
    invite_code = serializers.CharField(
        required=False,
        validators=[validate_invite_code_format]
    )
    
    def validate_name(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("스터디명을 입력해주세요.")
        return value.strip()
    
    def validate_invite_code(self, value):
        if value and not re.match(r'^[A-Z0-9]{8}$', value):
            raise serializers.ValidationError("초대 코드 형식이 올바르지 않습니다.")
        return value

# 서비스 레벨 응집도 예시 - 전체 폼 검증
class StudyCreateService:
    @staticmethod
    def validate_and_create(owner, data):
        """스터디 생성 전 전체 데이터 검증"""
        errors = {}
        
        if not data.get('name') or len(data['name'].strip()) == 0:
            errors['name'] = "스터디명을 입력해주세요."
        
        if data.get('daily_problem_count', 0) <= 0:
            errors['daily_problem_count'] = "일일 문제 수는 1 이상이어야 합니다."
        
        if errors:
            raise ValidationError(errors)
        
        return Study.objects.create(owner=owner, **data)
```

### Coupling

코드베이스의 다른 부분 간 의존성을 최소화합니다.

#### Balancing Abstraction and Coupling

**Rule:** 사용 사례가 분기될 수 있다면 중복의 조기 추상화를 피합니다. 낮은 결합도를 선호합니다.

**Guidance:** 추상화하기 전에 로직이 정말 동일하고 모든 사용 사례에서 동일하게 유지될 가능성이 높은지 고려하세요. 분기가 가능하다면, 초기에 로직을 분리해두는 것이 더 유지보수 가능하고 결합도가 낮은 코드로 이어질 수 있습니다.

#### Scoping Business Logic

**Rule:** 광범위한 비즈니스 로직을 더 작고 집중된 서비스/유틸리티로 분해합니다.

```python
# services/study_membership.py - 멤버십 관련 로직만 집중
class StudyMembershipService:
    """스터디 멤버십 관련 비즈니스 로직"""
    
    @staticmethod
    def join_study_by_invite_code(user, invite_code):
        """초대 코드로 스터디 가입"""
        study = Study.objects.get(invite_code=invite_code)
        if StudyMember.objects.filter(study=study, user=user).exists():
            raise ValueError("이미 가입된 스터디입니다.")
        return StudyMember.objects.create(
            study=study,
            user=user,
            role=StudyRole.MEMBER
        )
    
    @staticmethod
    def leave_study(user, study):
        """스터디 탈퇴"""
        if study.owner == user:
            raise ValueError("스터디 소유자는 탈퇴할 수 없습니다.")
        StudyMember.objects.filter(study=study, user=user).delete()

# services/study_assignment.py - 과제 관련 로직만 집중
class StudyAssignmentService:
    """스터디 과제 관련 비즈니스 로직"""
    
    @staticmethod
    def create_daily_assignment(study, problem, assigned_date, is_custom=False):
        """일일 과제 생성"""
        if DailyAssignment.objects.filter(
            study=study,
            problem=problem,
            assigned_date=assigned_date
        ).exists():
            raise ValueError("이미 해당 날짜에 할당된 문제입니다.")
        return DailyAssignment.objects.create(
            study=study,
            problem=problem,
            assigned_date=assigned_date,
            is_custom=is_custom
        )
```

#### Eliminating Cross-Module Dependencies

**Rule:** 모듈 간 직접 의존성을 줄이기 위해 인터페이스나 이벤트 기반 아키텍처를 사용합니다.

```python
# services/study_service.py - 스터디 생성 로직
class StudyService:
    @staticmethod
    def create_study(owner, name, description, **kwargs):
        """스터디 생성 및 초기 설정"""
        study = Study.objects.create(
            owner=owner,
            name=name,
            description=description,
            **kwargs
        )
        # 멤버십 서비스를 직접 호출하지 않고, 필요한 로직을 여기서 처리
        StudyMember.objects.create(
            study=study,
            user=owner,
            role=StudyRole.OWNER
        )
        return study

# views.py - 뷰는 필요한 서비스만 호출
class StudyCreateView(CreateAPIView):
    serializer_class = StudySerializer
    
    def perform_create(self, serializer):
        study = StudyService.create_study(
            owner=self.request.user,
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            **serializer.validated_data
        )
        serializer.instance = study
```
