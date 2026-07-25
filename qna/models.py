from django.conf import settings
from django.db import models


class Question(models.Model):
    """학생이 멘토에게 남기는 질문입니다."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="작성자",
    )

    content = models.TextField(
        verbose_name="질문 내용",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="작성일",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "질문"
        verbose_name_plural = "질문"

    def __str__(self):
        return self.content[:40]


class Answer(models.Model):
    """멘토가 질문에 남기는 답변입니다. 질문 하나에 답변 하나입니다."""

    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name="answer",
        verbose_name="질문",
    )

    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="답변자",
    )

    content = models.TextField(
        verbose_name="답변 내용",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="작성일",
    )

    class Meta:
        verbose_name = "답변"
        verbose_name_plural = "답변"

    def __str__(self):
        return self.content[:40]
