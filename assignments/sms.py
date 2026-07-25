import datetime
import hashlib
import hmac
import logging
import uuid

import requests
from django.conf import settings

from .models import Profile

logger = logging.getLogger(__name__)

COOLSMS_SEND_URL = "https://api.coolsms.co.kr/messages/v4/send"


def _auth_header():
    """CoolSMS(솔라피) v4 API의 HMAC-SHA256 인증 헤더를 만듭니다."""

    date = datetime.datetime.now(datetime.timezone.utc).isoformat()
    salt = uuid.uuid4().hex

    signature = hmac.new(
        settings.COOLSMS_API_SECRET.encode(),
        (date + salt).encode(),
        hashlib.sha256,
    ).hexdigest()

    return (
        f"HMAC-SHA256 apiKey={settings.COOLSMS_API_KEY}, "
        f"date={date}, salt={salt}, signature={signature}"
    )


def send_sms(to, text):
    """단일 수신자에게 문자를 보냅니다. 실패해도 예외를 밖으로 던지지 않습니다."""

    if not settings.COOLSMS_API_KEY or not settings.COOLSMS_API_SECRET:
        logger.warning("CoolSMS API 키가 설정되지 않아 문자를 보내지 않습니다.")
        return

    try:
        response = requests.post(
            COOLSMS_SEND_URL,
            json={
                "message": {
                    "to": to,
                    "from": settings.COOLSMS_SENDER,
                    "text": text,
                }
            },
            headers={
                "Authorization": _auth_header(),
            },
            timeout=10,
        )

        if response.status_code != 200:
            logger.error(
                "문자 발송 실패 (status=%s): %s",
                response.status_code,
                response.text,
            )
    except requests.RequestException:
        logger.exception("문자 발송 요청 중 오류가 발생했습니다.")


def _mentee_phones():
    return list(
        Profile.objects.filter(role=Profile.Role.MENTEE)
        .exclude(phone="")
        .values_list("phone", flat=True)
    )


def send_new_assignment_sms(assignment):
    """멘토가 과제를 등록하면 학생에게 알림 문자를 보냅니다."""

    for phone in _mentee_phones():
        send_sms(
            phone,
            (
                f"[개발노트] 새 과제가 등록되었습니다: {assignment.title}\n"
                f"https://mentationlab.tech/assignments/{assignment.pk}/"
            ),
        )


def send_submission_completed_sms(submission):
    """학생이 제출을 완료하면 과제를 낸 멘토에게 알림 문자를 보냅니다."""

    try:
        mentor_phone = submission.assignment.created_by.profile.phone
    except Profile.DoesNotExist:
        mentor_phone = ""

    if not mentor_phone:
        logger.warning("멘토의 휴대폰 번호가 없어 문자를 보내지 않습니다.")
        return

    send_sms(
        mentor_phone,
        (
            f"[개발노트] {submission.student.username}님이 과제를 제출했습니다: "
            f"{submission.assignment.title}\n"
            f"https://mentationlab.tech/assignments/{submission.assignment.pk}/"
        ),
    )
