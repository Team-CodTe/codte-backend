# Codte Backend

Django 기반 백엔드 프로젝트입니다. Poetry를 사용하여 의존성을 관리합니다.

## 📋 요구사항

- Python 3.13 이상
- Poetry (의존성 관리 도구)

## 🚀 시작하기

### 1. Poetry 설치

Poetry가 설치되어 있지 않은 경우, 다음 명령어로 설치할 수 있습니다:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

설치 후, Poetry를 PATH에 추가해야 합니다:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

또는 셸 설정 파일(`~/.zshrc` 또는 `~/.bashrc`)에 다음을 추가하세요:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 2. 프로젝트 클론 및 이동

```bash
git clone <repository-url>
cd codte-backend
```

### 3. 의존성 설치

Poetry를 사용하여 프로젝트 의존성을 설치합니다:

```bash
poetry install
```

이 명령어는 가상환경을 자동으로 생성하고 필요한 패키지들을 설치합니다.

### 4. 데이터베이스 마이그레이션

데이터베이스를 초기화합니다:

```bash
poetry run python manage.py migrate
```

### 5. 개발 서버 실행

Django 개발 서버를 시작합니다:

```bash
poetry run python manage.py runserver
```

서버가 실행되면 브라우저에서 `http://127.0.0.1:8000/` 또는 `http://localhost:8000/`로 접속할 수 있습니다.

## 📁 프로젝트 구조

```
codte-backend/
├── config/              # Django 프로젝트 설정 디렉토리
│   ├── __init__.py
│   ├── settings.py      # 프로젝트 설정
│   ├── urls.py          # URL 라우팅 설정
│   ├── wsgi.py          # WSGI 설정
│   └── asgi.py          # ASGI 설정
├── manage.py            # Django 관리 스크립트
├── pyproject.toml       # Poetry 의존성 관리 파일
├── poetry.lock          # 의존성 잠금 파일
└── README.md            # 프로젝트 문서
```

## 🛠️ 주요 명령어

### Poetry 명령어

```bash
# 의존성 설치
poetry install

# 새 패키지 추가
poetry add <package-name>

# 개발 의존성 추가
poetry add --group dev <package-name>

# 패키지 제거
poetry remove <package-name>

# 가상환경 활성화
poetry shell

# 의존성 업데이트
poetry update
```

### Django 명령어

모든 Django 명령어는 `poetry run`을 앞에 붙여서 실행합니다:

```bash
# 개발 서버 실행
poetry run python manage.py runserver

# 마이그레이션 생성
poetry run python manage.py makemigrations

# 마이그레이션 적용
poetry run python manage.py migrate

# 관리자 계정 생성
poetry run python manage.py createsuperuser

# Django 셸 실행
poetry run python manage.py shell

# 프로젝트 체크
poetry run python manage.py check
```

## 🔐 관리자 페이지

Django 관리자 페이지에 접근하려면:

1. 관리자 계정을 생성합니다:
   ```bash
   poetry run python manage.py createsuperuser
   ```

2. 서버를 실행한 후 `http://127.0.0.1:8000/admin/`로 접속합니다.

## 📦 현재 설치된 패키지

- Django 5.2.8

## 🔧 개발 환경 설정

### 가상환경 사용

Poetry는 자동으로 가상환경을 관리합니다. 가상환경을 직접 활성화하려면:

```bash
poetry shell
```

가상환경을 활성화한 후에는 `poetry run` 없이 직접 명령어를 실행할 수 있습니다:

```bash
python manage.py runserver
```

## 📝 참고사항

- 데이터베이스는 기본적으로 SQLite를 사용합니다 (`db.sqlite3`)
- 개발 환경에서는 `DEBUG = True`로 설정되어 있습니다
- 프로덕션 배포 전에는 반드시 `SECRET_KEY`를 변경하고 `DEBUG = False`로 설정하세요

## 🐛 문제 해결

### Poetry 명령어를 찾을 수 없는 경우

Poetry가 PATH에 추가되지 않은 경우, 다음을 확인하세요:

```bash
# Poetry 경로 확인
echo $HOME/.local/bin

# PATH에 추가
export PATH="$HOME/.local/bin:$PATH"
```

### 포트가 이미 사용 중인 경우

다른 포트로 서버를 실행할 수 있습니다:

```bash
poetry run python manage.py runserver 8001
```

## 📄 라이선스

이 프로젝트의 라이선스 정보는 프로젝트 소유자에게 문의하세요.

