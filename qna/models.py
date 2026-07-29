"""질의응답(QnA) 앱의 데이터 구조 정의.

- Question: 학생이 남기는 질문
- Answer: 멘토가 남기는 답변 (질문 1개당 답변 1개)
"""

from django.conf import settings
from django.db import models


class Question(models.Model):
    """학생이 멘토에게 남기는 질문입니다."""

    # 질문을 쓴 학생
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
        ordering = ["-created_at"]  # 최신 질문이 먼저
        verbose_name = "질문"
        verbose_name_plural = "질문"

    def __str__(self):
        # 별도 제목이 없으므로 내용 앞 40자를 제목처럼 사용
        return self.content[:40]


class Answer(models.Model):
    """멘토가 질문에 남기는 답변입니다. 질문 하나에 답변 하나입니다."""

    # OneToOne: 질문 하나에 답변은 하나만 존재. question.answer로 접근 가능.
    # 질문이 삭제되면 답변도 함께 삭제(CASCADE).
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name="answer",
        verbose_name="질문",
    )

    # 답변을 쓴 멘토
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
