"""과제 앱의 데이터 구조 정의.

- Profile: 사용자에게 멘토/멘티 역할과 휴대폰 번호를 부여
- Assignment: 멘토가 등록하는 과제
- Submission: 학생(멘티)이 과제에 제출하는 수행 결과
"""

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """사용자의 역할(멘토/멘티)을 구분하는 프로필입니다."""

    # 역할 선택지: DB에는 "mentor"/"mentee"로 저장되고, 화면엔 "멘토"/"멘티"로 표시
    class Role(models.TextChoices):
        MENTOR = "mentor", "멘토"
        MENTEE = "mentee", "멘티"

    # 사용자 1명당 프로필 1개 (OneToOne). user.profile로 접근 가능.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="사용자",
    )

    # 기본값은 멘티. 멘토 지정은 관리자 페이지에서 변경.
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MENTEE,
        verbose_name="역할",
    )

    # CoolSMS 문자 알림을 받을 번호. 비어 있으면 문자를 보내지 않음.
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

    # 과제를 등록한 멘토
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="출제자",
    )

    # 마감일은 선택 입력 (null=True: DB에 비어있는 값 허용)
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

    # 제출 상태: 진행중(임시 저장) / 완료(최종 제출)
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "진행중"
        COMPLETED = "completed", "완료"

    # 어떤 과제에 대한 제출물인지
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="과제",
    )

    # 제출한 학생
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="학생",
    )

    content = models.TextField(
        verbose_name="수행 내용",
    )

    # 첨부파일은 media/submissions/연도/월/ 폴더에 저장됨
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

        # 한 학생은 한 과제에 제출물을 하나만 가질 수 있음 (DB 차원에서 중복 방지)
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"],
                name="unique_submission_per_student",
            ),
        ]

    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"
