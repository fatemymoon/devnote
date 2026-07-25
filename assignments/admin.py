from django.contrib import admin

from .models import Assignment, Profile, Submission


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
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
