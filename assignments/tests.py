from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import sms
from .models import Assignment, Profile, Submission

User = get_user_model()


class RoleSetupMixin:
    """멘토/멘티 계정과 과제 하나를 만들어 두는 공통 준비 코드입니다."""

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

        self.assignment = Assignment.objects.create(
            title="테스트 과제",
            description="설명",
            created_by=self.mentor,
        )


class AssignmentFlowTests(RoleSetupMixin, TestCase):
    """멘토/멘티 역할별 권한과 문자 알림 트리거를 검증합니다."""

    def test_login_required(self):
        response = self.client.get(reverse("assignments:list"))
        self.assertEqual(response.status_code, 302)

    def test_mentee_cannot_create_assignment(self):
        self.client.login(username="student", password="pass1234")

        response = self.client.get(reverse("assignments:create"))
        self.assertEqual(response.status_code, 403)

    @patch("assignments.views.send_new_assignment_sms")
    def test_mentor_creates_assignment_and_sms_sent(self, mock_send):
        self.client.login(username="mentor", password="pass1234")

        response = self.client.post(
            reverse("assignments:create"),
            {
                "title": "새 과제",
                "description": "내용",
            },
        )

        self.assertEqual(response.status_code, 302)
        mock_send.assert_called_once()

    @patch("assignments.views.send_submission_completed_sms")
    def test_mentee_submission_complete_sends_sms(self, mock_send):
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
        mock_send.assert_called_once()

    @patch("assignments.views.send_submission_completed_sms")
    def test_mentee_draft_does_not_send_sms(self, mock_send):
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
        mock_send.assert_not_called()

    @patch("assignments.views.send_submission_completed_sms")
    def test_completed_resubmit_does_not_send_duplicate_sms(self, mock_send):
        self.client.login(username="student", password="pass1234")

        for _ in range(2):
            self.client.post(
                reverse("assignments:detail", args=[self.assignment.pk]),
                {
                    "content": "완료 내용",
                    "action": "complete",
                },
            )

        mock_send.assert_called_once()

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


class BoardAndWorkspaceTests(RoleSetupMixin, TestCase):
    """게시판형 과제목록과 역할별 작업 화면을 검증합니다."""

    def test_board_uses_board_template_for_both_roles(self):
        for username in ["mentor", "student"]:
            self.client.login(username=username, password="pass1234")

            response = self.client.get(reverse("assignments:list"))

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response,
                "assignments/assignment_list.html",
            )

    def test_board_search_filters_results(self):
        Assignment.objects.create(
            title="Docker 볼륨 정리",
            description="설명",
            created_by=self.mentor,
        )

        self.client.login(username="student", password="pass1234")

        response = self.client.get(
            reverse("assignments:list"),
            {"q": "Docker"},
        )

        self.assertContains(response, "Docker 볼륨 정리")
        self.assertNotContains(response, "테스트 과제")

    def test_board_paginates_by_20(self):
        for i in range(25):
            Assignment.objects.create(
                title=f"과제 {i}",
                description="설명",
                created_by=self.mentor,
            )

        self.client.login(username="student", password="pass1234")

        response = self.client.get(reverse("assignments:list"))
        self.assertEqual(len(response.context["rows"]), 20)

        response = self.client.get(
            reverse("assignments:list"),
            {"page": 2},
        )
        self.assertEqual(len(response.context["rows"]), 6)

    def test_mentee_workspace_puts_unsubmitted_first(self):
        submitted = Assignment.objects.create(
            title="제출한 과제",
            description="설명",
            created_by=self.mentor,
        )
        Submission.objects.create(
            assignment=submitted,
            student=self.student,
            content="내용",
            status=Submission.Status.COMPLETED,
        )

        self.client.login(username="student", password="pass1234")

        response = self.client.get(reverse("assignments:workspace"))

        rows = response.context["rows"]
        self.assertEqual(rows[0]["assignment"], self.assignment)
        self.assertEqual(rows[-1]["assignment"], submitted)

    def test_mentor_workspace_shows_only_own_assignments(self):
        other_mentor = User.objects.create_user(
            username="mentor2",
            password="pass1234",
        )
        Profile.objects.create(
            user=other_mentor,
            role=Profile.Role.MENTOR,
        )
        Assignment.objects.create(
            title="다른 멘토 과제",
            description="설명",
            created_by=other_mentor,
        )

        self.client.login(username="mentor", password="pass1234")

        response = self.client.get(reverse("assignments:workspace"))

        titles = [a.title for a in response.context["assignments"]]
        self.assertIn("테스트 과제", titles)
        self.assertNotIn("다른 멘토 과제", titles)


class SmsRecipientTests(RoleSetupMixin, TestCase):
    """문자 수신자 선정 로직을 검증합니다."""

    @patch("assignments.sms.send_sms")
    def test_new_assignment_sms_goes_to_mentee_phones(self, mock_send):
        sms.send_new_assignment_sms(self.assignment)

        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], "01033334444")

    @patch("assignments.sms.send_sms")
    def test_completed_sms_goes_to_mentor_phone(self, mock_send):
        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content="완료",
            status=Submission.Status.COMPLETED,
        )

        sms.send_submission_completed_sms(submission)

        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], "01011112222")

    @patch("assignments.sms.send_sms")
    def test_no_sms_when_mentor_has_no_phone(self, mock_send):
        self.mentor.profile.phone = ""
        self.mentor.profile.save()

        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content="완료",
            status=Submission.Status.COMPLETED,
        )

        sms.send_submission_completed_sms(submission)

        mock_send.assert_not_called()
