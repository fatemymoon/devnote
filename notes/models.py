"""개발노트 앱의 데이터 구조(DB 테이블) 정의."""

from django.conf import settings
from django.db import models


class Note(models.Model):
    """개발 과정에서 작성하는 노트입니다. (노트 1개 = DB의 행 1개)"""

    # 노트 작성자. 사용자가 탈퇴(삭제)되면 그 사람의 노트도 함께 삭제(CASCADE).
    # related_name="notes" → user.notes.all()로 이 사용자의 노트를 조회 가능.
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

    # 분류용 카테고리 (예: Django, Linux). blank=True → 비워둘 수 있음.
    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="카테고리",
    )

    # 쉼표로 구분한 태그 문자열 (검색에 활용)
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="태그",
        help_text="여러 태그는 쉼표로 구분하세요.",
    )

    # 중요 표시. True인 노트는 목록 맨 위에 고정됩니다.
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="중요 노트",
    )

    # auto_now_add: 처음 저장할 때 한 번만 자동 기록
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="작성일",
    )

    # auto_now: 저장할 때마다 현재 시각으로 자동 갱신
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정일",
    )

    class Meta:
        # 기본 정렬: 고정 노트 먼저, 그다음 최근 수정 순
        ordering = ["-is_pinned", "-updated_at"]
        verbose_name = "개발노트"          # 관리자 페이지에 표시될 이름
        verbose_name_plural = "개발노트"

    def __str__(self):
        # 관리자 페이지 등에서 이 객체를 표시할 때 제목을 사용
        return self.title