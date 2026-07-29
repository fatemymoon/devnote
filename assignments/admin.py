"""관리자 페이지(/admin/)에서 프로필/과제/제출물을 관리하기 위한 설정.

특히 Profile은 여기서 사용자의 역할(멘토/멘티)과 휴대폰 번호를 지정합니다.
"""

from django.contrib import admin

from .models import Assignment, Profile, Submission


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "phone",
    )

    list_filter = (
        "role",
    )


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "created_by",
        "due_date",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "student",
        "status",
        "submitted_at",
        "updated_at",
    )

    list_filter = (
        "status",
    )
