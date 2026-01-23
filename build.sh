#!/usr/bin/env bash
# Render 빌드 스크립트
# 참고: https://render.com/docs/deploy-django

set -o errexit  # 에러 발생 시 스크립트 중단

# Poetry 설치
pip install poetry

# 의존성 설치 (가상환경 없이 시스템에 직접 설치)
poetry config virtualenvs.create false
poetry install --only main --no-interaction --no-ansi

# 정적 파일 수집
python manage.py collectstatic --no-input

# 데이터베이스 마이그레이션
python manage.py migrate --no-input
