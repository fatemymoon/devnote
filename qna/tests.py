from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from assignments.models import Profile

from . import notifications
from .models import Answer, Question

User = get_user_model()


class QnaSetupMixin:
    """멘토/멘티 계정을 만들어 두는 공통 준비 코드입니다."""

    def setUp(self):
        self.mentor = User.objects.create_user(
            username="mentor",
            password="pass1234",
        )
        Profile.objects.create(
            user=self.mentor,
            role=Profile.Role.MENTOR,
            phone="01011112222",
        )

        self.student = User.objects.create_user(
            username="student",
            password="pass1234",
        )
        Profile.objects.create(
            user=self.student,
            role=Profile.Role.MENTEE,
            phone="01033334444",
        )


class QuestionFlowTests(QnaSetupMixin, TestCase):
    """질문/답변 권한과 문자 알림 트리거를 검증합니다."""

    def test_login_required(self):
        response = self.client.get(reverse("qna:list"))
        self.assertEqual(response.status_code, 302)

    def test_mentor_cannot_create_question(self):
        self.client.login(username="mentor", password="pass1234")

        response = self.client.get(reverse("qna:create"))
        self.assertEqual(response.status_code, 403)

    @patch("qna.views.send_new_question_sms")
    def test_student_creates_question_and_sms_sent(self, mock_send):
        self.client.login(username="student", password="pass1234")

        response = self.client.post(
            reverse("qna:create"),
            {
                "content": "질문 있습니다.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Question.objects.filter(student=self.student).exists()
        )
        mock_send.assert_called_once()

    @patch("qna.views.send_new_answer_sms")
    def test_mentor_answers_and_sms_sent(self, mock_send):
        question = Question.objects.create(
            student=self.student,
            content="질문",
        )

        self.client.login(username="mentor", password="pass1234")

        response = self.client.post(
            reverse("qna:detail", args=[question.pk]),
            {
                "content": "답변입니다.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(hasattr(question, "answer") or Answer.objects.filter(question=question).exists())
        mock_send.assert_called_once()

    @patch("qna.views.send_new_answer_sms")
    def test_answer_update_does_not_resend_sms(self, mock_send):
        question = Question.objects.create(
            student=self.student,
            content="질문",
        )
        Answer.objects.create(
            question=question,
            mentor=self.mentor,
            content="첫 답변",
        )

        self.client.login(username="mentor", password="pass1234")

        response = self.client.post(
            reverse("qna:detail", args=[question.pk]),
            {
                "content": "수정된 답변",
            },
        )

        self.assertEqual(response.status_code, 302)

        answer = Answer.objects.get(question=question)
        self.assertEqual(answer.content, "수정된 답변")
        self.assertEqual(Answer.objects.filter(question=question).count(), 1)
        mock_send.assert_not_called()

    def test_student_cannot_see_others_question(self):
        other = User.objects.create_user(
            username="other",
            password="pass1234",
        )
        Profile.objects.create(
            user=other,
            role=Profile.Role.MENTEE,
        )
        question = Question.objects.create(
            student=other,
            content="다른 학생 질문",
        )

        self.client.login(username="student", password="pass1234")

        response = self.client.get(
            reverse("qna:detail", args=[question.pk]),
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("qna:delete", args=[question.pk]),
        )
        self.assertEqual(response.status_code, 404)

    def test_mentor_sees_all_questions_in_list(self):
        Question.objects.create(
            student=self.student,
            content="학생 질문입니다",
        )

        self.client.login(username="mentor", password="pass1234")

        response = self.client.get(reverse("qna:list"))
        self.assertContains(response, "학생 질문입니다")


class QnaNotificationTests(QnaSetupMixin, TestCase):
    """문자 수신자 선정 로직을 검증합니다."""

    @patch("qna.notifications.send_sms")
    def test_new_question_sms_goes_to_mentor(self, mock_send):
        question = Question.objects.create(
            student=self.student,
            content="질문",
        )

        notifications.send_new_question_sms(question)

        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], "01011112222")

    @patch("qna.notifications.send_sms")
    def test_new_answer_sms_goes_to_student(self, mock_send):
        question = Question.objects.create(
            student=self.student,
            content="질문",
        )
        answer = Answer.objects.create(
            question=question,
            mentor=self.mentor,
            content="답변",
        )

        notifications.send_new_answer_sms(answer)

        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], "01033334444")
