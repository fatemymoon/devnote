import logging

from django.core.mail import send_mail

from .models import Profile

logger = logging.getLogger(__name__)


def _mentee_emails():
    return list(
        Profile.objects.filter(role=Profile.Role.MENTEE)
        .exclude(user__email="")
        .values_list("user__email", flat=True)
    )


def send_new_assignment_email(assignment):
    """멘토가 과제를 등록하면 학생에게 알림 이메일을 보냅니다."""

    recipients = _mentee_emails()

    if not recipients:
        return

    try:
        send_mail(
            subject=f"[개발노트] 새 과제가 등록되었습니다: {assignment.title}",
            message=(
                f"새 과제가 등록되었습니다.\n\n"
                f"제목: {assignment.title}\n"
                f"마감일: {assignment.due_date or '없음'}\n\n"
                f"{assignment.description}\n\n"
                f"사이트에서 확인하세요: https://mentationlab.tech/assignments/{assignment.pk}/"
            ),
            from_email=None,
            recipient_list=recipients,
        )
    except Exception:
        logger.exception("새 과제 알림 이메일 발송에 실패했습니다.")


def send_submission_completed_email(submission):
    """학생이 제출을 완료하면 과제를 낸 멘토에게 알림 이메일을 보냅니다."""

    mentor_email = submission.assignment.created_by.email

    if not mentor_email:
        return

    try:
        send_mail(
            subject=(
                f"[개발노트] {submission.student.username}님이 "
                f"과제를 제출했습니다: {submission.assignment.title}"
            ),
            message=(
                f"{submission.student.username}님이 과제를 완료 상태로 제출했습니다.\n\n"
                f"과제: {submission.assignment.title}\n\n"
                f"사이트에서 확인하세요: "
                f"https://mentationlab.tech/assignments/{submission.assignment.pk}/"
            ),
            from_email=None,
            recipient_list=[mentor_email],
        )
    except Exception:
        logger.exception("과제 제출 알림 이메일 발송에 실패했습니다.")
