"""질의응답 관련 문자 알림.

실제 발송 로직(send_sms)은 assignments/sms.py의 것을 재사용하고,
여기서는 "누구에게 어떤 내용을 보낼지"만 정합니다.
"""

import logging

from assignments.models import Profile
from assignments.sms import send_sms

logger = logging.getLogger(__name__)


def _mentor_phones():
    """번호가 등록된 모든 멘토의 휴대폰 번호 목록을 가져옵니다."""
    return list(
        Profile.objects.filter(role=Profile.Role.MENTOR)
        .exclude(phone="")
        .values_list("phone", flat=True)
    )


def send_new_question_sms(question):
    """학생이 질문을 등록하면 멘토에게 알림 문자를 보냅니다."""

    for phone in _mentor_phones():
        send_sms(
            phone,
            (
                f"[개발노트] {question.student.username}님이 질문을 남겼습니다.\n"
                f"https://mentationlab.tech/qna/{question.pk}/"
            ),
        )


def send_new_answer_sms(answer):
    """멘토가 답변을 달면 질문을 쓴 학생에게 알림 문자를 보냅니다."""

    # 질문을 쓴 학생의 번호를 찾음. 프로필이 없을 수도 있으므로 예외 처리.
    try:
        student_phone = answer.question.student.profile.phone
    except Profile.DoesNotExist:
        student_phone = ""

    if not student_phone:
        logger.warning("학생의 휴대폰 번호가 없어 문자를 보내지 않습니다.")
        return

    send_sms(
        student_phone,
        (
            f"[개발노트] 질문에 답변이 등록되었습니다.\n"
            f"https://mentationlab.tech/qna/{answer.question.pk}/"
        ),
    )
