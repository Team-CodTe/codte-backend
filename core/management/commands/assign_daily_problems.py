"""
일일 문제 배정 Management Command

매일 오전 6시에 cron으로 실행하여 모든 스터디에 문제를 배정합니다.

사용법:
    # 모든 스터디에 오늘 문제 배정
    python manage.py assign_daily_problems

    # 특정 날짜에 문제 배정
    python manage.py assign_daily_problems --date 2024-12-25

    # 특정 스터디에만 문제 배정
    python manage.py assign_daily_problems --study-id 1

Cron 설정 예시 (매일 오전 6시):
    0 6 * * * cd /path/to/project && poetry run python manage.py assign_daily_problems
"""

from datetime import date

from django.core.management.base import BaseCommand

from core.assignments.services import DailyAssignmentService


class Command(BaseCommand):
    help = "모든 스터디에 일일 문제를 배정합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            help="배정 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)",
        )
        parser.add_argument(
            "--study-id",
            type=int,
            help="특정 스터디 ID만 처리",
        )

    def handle(self, *args, **options):
        service = DailyAssignmentService()

        # 날짜 파싱
        target_date = date.today()
        if options["date"]:
            try:
                target_date = date.fromisoformat(options["date"])
            except ValueError:
                self.stderr.write(
                    self.style.ERROR(
                        f"잘못된 날짜 형식입니다: {options['date']} (YYYY-MM-DD 형식 필요)"
                    )
                )
                return

        self.stdout.write(f"일일 문제 배정을 시작합니다. (날짜: {target_date})")

        # 특정 스터디만 처리
        if options["study_id"]:
            from core.models import Study

            try:
                study = Study.objects.get(id=options["study_id"])
            except Study.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f"스터디를 찾을 수 없습니다: ID={options['study_id']}"
                    )
                )
                return

            try:
                assignments = service.assign_daily_problems(study, target_date)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ 스터디 '{study.name}'에 {len(assignments)}개 문제 배정 완료"
                    )
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"✗ 스터디 '{study.name}' 실패: {e}")
                )
            return

        # 모든 스터디 처리
        results = service.assign_all_studies(target_date)

        success_count = 0
        error_count = 0

        for study_id, result in results.items():
            if result["status"] == "success":
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ 스터디 '{result['study_name']}' (ID={study_id}): "
                        f"{result['count']}개 문제 배정"
                    )
                )
            else:
                error_count += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"✗ 스터디 '{result['study_name']}' (ID={study_id}): "
                        f"{result['message']}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"완료: 성공 {success_count}개, 실패 {error_count}개")
