"""관리자 페이지(/admin/)에서 질문/답변을 관리하기 위한 설정."""

from django.contrib import admin

from .models import Answer, Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "student",
        "created_at",
    )

    search_fields = (
        "content",
    )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "question",
        "mentor",
        "created_at",
    )

    search_fields = (
        "content",
    )
