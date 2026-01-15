from rest_framework import serializers


class AssignmentStatusQuerySerializer(serializers.Serializer):
    """문제 풀이 상태 조회 Query Serializer"""

    date = serializers.DateField(
        required=False, allow_null=True, help_text="날짜 (YYYY-MM-DD, 기본값: 오늘)"
    )
    view = serializers.ChoiceField(
        choices=["me", "group"],
        default="me",
        required=False,
        help_text="조회 방식 (me: 현재 사용자, group: 모든 멤버)",
    )


class StatisticsQuerySerializer(serializers.Serializer):
    """통계 조회 Query Serializer"""

    view = serializers.ChoiceField(
        choices=["me", "group", "member"],
        default="me",
        required=False,
        help_text="조회 방식 (me: 현재 사용자, group: 모든 멤버, member: 특정 멤버)",
    )
    member_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="멤버 ID (view=member일 때 필수)",
    )
    start_date = serializers.DateField(
        required=False, allow_null=True, help_text="시작 날짜 (YYYY-MM-DD)"
    )
    end_date = serializers.DateField(
        required=False, allow_null=True, help_text="종료 날짜 (YYYY-MM-DD)"
    )

    def validate(self, data):
        """view=member일 때 member_id 필수 검증"""
        if data.get("view") == "member" and not data.get("member_id"):
            raise serializers.ValidationError(
                {"member_id": "view='member'일 때 member_id가 필요합니다."}
            )
        return data


class ProblemStatusSerializer(serializers.Serializer):
    """문제 풀이 상태 Serializer"""

    problem_id = serializers.IntegerField()
    boj_number = serializers.IntegerField()
    title = serializers.CharField()
    problem_status = serializers.CharField()
    note_status = serializers.CharField()
    last_updated_at = serializers.DateTimeField(allow_null=True)


class MemberStatusSerializer(serializers.Serializer):
    """멤버 상태 Serializer"""

    member_id = serializers.IntegerField()
    member_email = serializers.EmailField()
    username = serializers.CharField(allow_null=True)
    boj_username = serializers.CharField(allow_null=True)
    problem_status = serializers.CharField()
    note_status = serializers.CharField()
    last_updated_at = serializers.DateTimeField(allow_null=True)


class StatusSummarySerializer(serializers.Serializer):
    """상태 요약 Serializer"""

    not_attempted_count = serializers.IntegerField()
    in_progress_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()


class NoteStatusSummarySerializer(serializers.Serializer):
    """노트 상태 요약 Serializer"""

    not_completed_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()


class AssignmentStatusResponseSerializer(serializers.Serializer):
    """문제 풀이 상태 조회 응답 Serializer (view=me)"""

    date = serializers.DateField()
    view = serializers.CharField()
    assignments = ProblemStatusSerializer(many=True)
    total_count = serializers.IntegerField()
    problem_status_summary = StatusSummarySerializer()
    note_status_summary = NoteStatusSummarySerializer()
    can_update = serializers.BooleanField()
    next_available_at = serializers.DateTimeField(allow_null=True)
    last_updated_at = serializers.DateTimeField(allow_null=True)


class MemberWithAssignmentsSerializer(serializers.Serializer):
    """멤버와 과제 목록 Serializer"""

    member_id = serializers.IntegerField()
    member_email = serializers.EmailField()
    username = serializers.CharField(allow_null=True)
    boj_username = serializers.CharField(allow_null=True)
    assignments = ProblemStatusSerializer(many=True)
    problem_status_summary = StatusSummarySerializer()
    note_status_summary = NoteStatusSummarySerializer()
    total_count = serializers.IntegerField()


class OverallSummarySerializer(serializers.Serializer):
    """전체 요약 Serializer"""

    problem_status_summary = serializers.DictField()
    note_status_summary = serializers.DictField()


class GroupAssignmentStatusResponseSerializer(serializers.Serializer):
    """문제 풀이 상태 조회 응답 Serializer (view=group)"""

    date = serializers.DateField()
    view = serializers.CharField()
    members = MemberWithAssignmentsSerializer(many=True)
    total_members = serializers.IntegerField()
    overall_summary = OverallSummarySerializer()
    can_update = serializers.BooleanField()
    next_available_at = serializers.DateTimeField(allow_null=True)
    last_updated_at = serializers.DateTimeField(allow_null=True)


class ProblemMembersStatusResponseSerializer(serializers.Serializer):
    """특정 문제의 모든 멤버 풀이 상태 응답 Serializer"""

    problem_id = serializers.IntegerField()
    boj_number = serializers.IntegerField()
    title = serializers.CharField()
    members_status = MemberStatusSerializer(many=True)
    problem_status_summary = serializers.DictField()
    note_status_summary = serializers.DictField()


class DailyStatisticsSerializer(serializers.Serializer):
    """일별 통계 Serializer"""

    date = serializers.DateField()
    assigned_count = serializers.IntegerField()
    problem_status_summary = StatusSummarySerializer()
    note_status_summary = NoteStatusSummarySerializer()


class MyStatisticsResponseSerializer(serializers.Serializer):
    """통계 조회 응답 Serializer (view=me)"""

    view = serializers.CharField()
    member_id = serializers.IntegerField()
    member_email = serializers.EmailField()
    username = serializers.CharField(allow_null=True)
    boj_username = serializers.CharField(allow_null=True)
    total_assigned = serializers.IntegerField()
    problem_status_summary = StatusSummarySerializer()
    note_status_summary = NoteStatusSummarySerializer()
    problem_completion_rate = serializers.FloatField()
    note_completion_rate = serializers.FloatField()
    date_range = serializers.DictField()
    daily_statistics = DailyStatisticsSerializer(many=True)


class MemberStatisticsItemSerializer(serializers.Serializer):
    """멤버 통계 항목 Serializer"""

    member_id = serializers.IntegerField()
    member_email = serializers.EmailField()
    username = serializers.CharField(allow_null=True)
    boj_username = serializers.CharField(allow_null=True)
    total_assigned = serializers.IntegerField()
    problem_status_summary = StatusSummarySerializer()
    note_status_summary = NoteStatusSummarySerializer()
    problem_completion_rate = serializers.FloatField()
    note_completion_rate = serializers.FloatField()


class GroupStatisticsResponseSerializer(serializers.Serializer):
    """통계 조회 응답 Serializer (view=group)"""

    view = serializers.CharField()
    total_members = serializers.IntegerField()
    total_assigned = serializers.IntegerField()
    problem_status_summary = StatusSummarySerializer()
    note_status_summary = NoteStatusSummarySerializer()
    average_problem_completion_rate = serializers.FloatField()
    average_note_completion_rate = serializers.FloatField()
    date_range = serializers.DictField()
    members_statistics = MemberStatisticsItemSerializer(many=True)
    daily_statistics = DailyStatisticsSerializer(many=True)


class MemberStatisticsResponseSerializer(serializers.Serializer):
    """통계 조회 응답 Serializer (view=member)"""

    view = serializers.CharField()
    member_id = serializers.IntegerField()
    member_email = serializers.EmailField()
    username = serializers.CharField(allow_null=True)
    boj_username = serializers.CharField(allow_null=True)
    total_assigned = serializers.IntegerField()
    problem_status_summary = StatusSummarySerializer()
    note_status_summary = NoteStatusSummarySerializer()
    problem_completion_rate = serializers.FloatField()
    note_completion_rate = serializers.FloatField()
    date_range = serializers.DictField()
    daily_statistics = DailyStatisticsSerializer(many=True)


class UpdateCooldownErrorSerializer(serializers.Serializer):
    """상태 업데이트 쿨다운 에러 Serializer"""

    error_code = serializers.CharField()
    message = serializers.CharField()
    next_available_at = serializers.DateTimeField()
