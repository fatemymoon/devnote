from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Assignment, Profile, Submission

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AssignmentFlowTests(TestCase):
    """멘토/멘티 역할별 권한과 알림 이메일을 검증합니다."""

    def setUp(self):
        self.mentor = User.objects.create_user(
            username="mentor",
            password="pass1234",
            email="mentor@example.com",
        )
        Profile.objects.create(
            user=self.mentor,
            role=Profile.Role.MENTOR,
        )

        self.student = User.objects.create_user(
            username="student",
            password="pass1234",
            email="student@example.com",
        )
        Profile.objects.create(
            user=self.student,
            role=Profile.Role.MENTEE,
        )

        self.assignment = Assignment.objects.create(
            title="테스트 과제",
            description="설명",
            created_by=self.mentor,
        )

    def test_login_required(self):
        response = self.client.get(reverse("assignments:list"))
        self.assertEqual(response.status_code, 302)

    def test_mentee_cannot_create_assignment(self):
        self.client.login(username="student", password="pass1234")

        response = self.client.get(reverse("assignments:create"))
        self.assertEqual(response.status_code, 403)

    def test_mentor_creates_assignment_and_email_sent(self):
        self.client.login(username="mentor", password="pass1234")

        response = self.client.post(
            reverse("assignments:create"),
            {
                "title": "새 과제",
                "description": "내용",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("student@example.com", mail.outbox[0].to)

    def test_mentee_submission_complete_sends_email_to_mentor(self):
        self.client.login(username="student", password="pass1234")

        response = self.client.post(
            reverse("assignments:detail", args=[self.assignment.pk]),
            {
                "content": "과제 수행 결과",
                "action": "complete",
            },
        )

        self.assertEqual(response.status_code, 302)

        submission = Submission.objects.get(
            assignment=self.assignment,
            student=self.student,
        )
        self.assertEqual(submission.status, Submission.Status.COMPLETED)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("mentor@example.com", mail.outbox[0].to)

    def test_mentee_draft_does_not_send_email(self):
        self.client.login(username="student", password="pass1234")

        self.client.post(
            reverse("assignments:detail", args=[self.assignment.pk]),
            {
                "content": "임시저장 내용",
                "action": "save",
            },
        )

        submission = Submission.objects.get(
            assignment=self.assignment,
            student=self.student,
        )
        self.assertEqual(submission.status, Submission.Status.IN_PROGRESS)
        self.assertEqual(len(mail.outbox), 0)

    def test_completed_resubmit_does_not_send_duplicate_email(self):
        self.client.login(username="student", password="pass1234")

        for _ in range(2):
            self.client.post(
                reverse("assignments:detail", args=[self.assignment.pk]),
                {
                    "content": "완료 내용",
                    "action": "complete",
                },
            )

        self.assertEqual(len(mail.outbox), 1)

    def test_mentee_cannot_delete_other_students_submission(self):
        other = User.objects.create_user(
            username="other",
            password="pass1234",
        )
        Profile.objects.create(
            user=other,
            role=Profile.Role.MENTEE,
        )
        Submission.objects.create(
            assignment=self.assignment,
            student=other,
            content="다른 학생 제출물",
        )

        self.client.login(username="student", password="pass1234")

        response = self.client.post(
            reverse(
                "assignments:submission_delete",
                args=[self.assignment.pk],
            ),
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Submission.objects.filter(student=other).exists()
        )

    def test_mentor_sees_all_submissions_on_detail(self):
        Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content="학생 제출물",
            status=Submission.Status.COMPLETED,
        )

        self.client.login(username="mentor", password="pass1234")

        response = self.client.get(
            reverse("assignments:detail", args=[self.assignment.pk]),
        )

        self.assertContains(response, "학생 제출물")
        self.assertContains(response, "student")
