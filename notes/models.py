from django.conf import settings
from django.db import models


class Note(models.Model):
    """개발 과정에서 작성하는 노트입니다."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name="작성자",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="제목",
    )

    content = models.TextField(
        verbose_name="내용",
    )

    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="카테고리",
    )

    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="태그",
        help_text="여러 태그는 쉼표로 구분하세요.",
    )

    is_pinned = models.BooleanField(
        default=False,
        verbose_name="중요 노트",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="작성일",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정일",
    )

    class Meta:
        ordering = ["-is_pinned", "-updated_at"]
        verbose_name = "개발노트"
        verbose_name_plural = "개발노트"

    def __str__(self):
        return self.title