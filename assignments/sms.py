"""CoolSMS(솔라피) API를 이용한 문자(SMS) 발송 기능.

- 새 과제 등록 → 모든 학생에게 알림
- 과제 제출 완료 → 출제한 멘토에게 알림
API 키는 settings.py(환경 변수)에서 읽어옵니다.
"""

import datetime
import hashlib
import hmac
import logging
import uuid

import requests  # 외부 API에 HTTP 요청을 보내는 라이브러리
from django.conf import settings

from .models import Profile

logger = logging.getLogger(__name__)  # 발송 실패 등을 서버 로그에 기록

# CoolSMS 문자 발송 API 주소
COOLSMS_SEND_URL = "https://api.coolsms.co.kr/messages/v4/send"


def _auth_header():
    """CoolSMS(솔라피) v4 API의 HMAC-SHA256 인증 헤더를 만듭니다.

    현재 시각 + 랜덤 문자열(salt)을 API 시크릿으로 서명해서
    "이 요청은 진짜 API 키 주인이 보낸 것"임을 증명하는 방식입니다.
    """

    date = datetime.datetime.now(datetime.timezone.utc).isoformat()
    salt = uuid.uuid4().hex  # 요청마다 다른 랜덤 값 (재사용 공격 방지)

    # (날짜 + salt)를 시크릿 키로 HMAC-SHA256 서명
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
    """단일 수신자에게 문자를 보냅니다. 실패해도 예외를 밖으로 던지지 않습니다.

    문자 발송이 실패하더라도 과제 등록/제출 같은 원래 작업은
    정상적으로 완료되어야 하므로, 오류는 로그에만 남기고 조용히 넘어갑니다.
    """

    # API 키가 없으면 (개발 환경 등) 발송 자체를 건너뜀
    if not settings.COOLSMS_API_KEY or not settings.COOLSMS_API_SECRET:
        logger.warning("CoolSMS API 키가 설정되지 않아 문자를 보내지 않습니다.")
        return

    try:
        # CoolSMS API에 발송 요청 (10초 안에 응답 없으면 포기)
        response = requests.post(
            COOLSMS_SEND_URL,
            json={
                "message": {
                    "to": to,                        # 받는 번호
                    "from": settings.COOLSMS_SENDER, # 등록된 발신 번호
                    "text": text,                    # 문자 내용
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
        # 네트워크 오류 등: 로그만 남기고 원래 작업은 계속 진행
        logger.exception("문자 발송 요청 중 오류가 발생했습니다.")


def _mentee_phones():
    """번호가 등록된 모든 멘티(학생)의 휴대폰 번호 목록을 가져옵니다."""
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

    # 과제 출제자(멘토)의 번호를 찾음. 프로필이 없을 수도 있으므로 예외 처리.
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
