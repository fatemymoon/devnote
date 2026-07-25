from django.conf import settings
from django.db import models


class Profile(models.Model):
    """사용자의 역할(멘토/멘티)을 구분하는 프로필입니다."""

    class Role(models.TextChoices):
        MENTOR = "mentor", "멘토"
        MENTEE = "mentee", "멘티"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="사용자",
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MENTEE,
        verbose_name="역할",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="휴대폰 번호",
        help_text="문자 알림을 받을 번호입니다. 예: 01012345678",
    )

    class Meta:
        verbose_name = "프로필"
        verbose_name_plural = "프로필"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Assignment(models.Model):
    """멘토가 등록하는 과제입니다."""

    title = models.CharField(
        max_length=200,
        verbose_name="제목",
    )

    description = models.TextField(
        verbose_name="설명",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="출제자",
    )

    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="마감일",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="등록일",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정일",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "과제"
        verbose_name_plural = "과제"

    def __str__(self):
        return self.title


class Submission(models.Model):
    """학생이 과제에 대해 제출하는 수행 결과입니다."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "진행중"
        COMPLETED = "completed", "완료"

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="과제",
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="학생",
    )

    content = models.TextField(
        verbose_name="수행 내용",
    )

    attachment = models.FileField(
        upload_to="submissions/%Y/%m/",
        blank=True,
        verbose_name="첨부파일",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        verbose_name="상태",
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="제출일",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정일",
    )

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "제출물"
        verbose_name_plural = "제출물"

        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"],
                name="unique_submission_per_student",
            ),
        ]

    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"
