"""관리자 페이지(/admin/)에서 개발노트를 어떻게 보여줄지 설정."""

from django.contrib import admin

from .models import Note


@admin.register(Note)  # Note 모델을 관리자 페이지에 등록
class NoteAdmin(admin.ModelAdmin):
    # 목록 화면에 표시할 열
    list_display = (
        "title",
        "category",
        "author",
        "is_pinned",
        "created_at",
        "updated_at",
    )

    # 검색창이 뒤질 필드
    search_fields = (
        "title",
        "content",
        "category",
        "tags",
    )

    # 우측 사이드바 필터
    list_filter = (
        "category",
        "is_pinned",
        "created_at",
    )

    # 목록 정렬: 고정 노트 먼저, 최근 수정 순
    ordering = (
        "-is_pinned",
        "-updated_at",
    )