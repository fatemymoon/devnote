from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "author",
        "is_pinned",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "content",
        "category",
        "tags",
    )

    list_filter = (
        "category",
        "is_pinned",
        "created_at",
    )

    ordering = (
        "-is_pinned",
        "-updated_at",
    )