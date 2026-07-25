from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import is_mentor, mentee_required, mentor_required
from .sms import send_new_assignment_sms, send_submission_completed_sms
from .forms import AssignmentForm, SubmissionForm
from .models import Assignment, Submission


@login_required
def assignment_list(request):
    """과제 목록을 역할에 따라 다르게 보여줍니다."""

    if is_mentor(request.user):
        assignments = Assignment.objects.annotate(
            submission_count=Count("submissions"),
            completed_count=Count(
                "submissions",
                filter=Q(submissions__status=Submission.Status.COMPLETED),
            ),
        )

        return render(
            request,
            "assignments/assignment_list_mentor.html",
            {
                "assignments": assignments,
            },
        )

    assignments = Assignment.objects.all()

    my_submissions = {
        submission.assignment_id: submission
        for submission in Submission.objects.filter(student=request.user)
    }

    rows = [
        {
            "assignment": assignment,
            "submission": my_submissions.get(assignment.pk),
        }
        for assignment in assignments
    ]

    return render(
        request,
        "assignments/assignment_list_mentee.html",
        {
            "rows": rows,
        },
    )


@login_required
def assignment_detail(request, pk):
    """과제 내용을 보여주고, 학생에게는 제출 폼을 함께 보여줍니다."""

    assignment = get_object_or_404(Assignment, pk=pk)

    if is_mentor(request.user):
        submissions = assignment.submissions.select_related("student")

        return render(
            request,
            "assignments/assignment_detail_mentor.html",
            {
                "assignment": assignment,
                "submissions": submissions,
            },
        )

    submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user,
    ).first()

    if request.method == "POST":
        form = SubmissionForm(
            request.POST,
            request.FILES,
            instance=submission,
        )

        if form.is_valid():
            was_completed = (
                submission is not None
                and submission.status == Submission.Status.COMPLETED
            )

            new_submission = form.save(commit=False)
            new_submission.assignment = assignment
            new_submission.student = request.user

            if request.POST.get("action") == "complete":
                new_submission.status = Submission.Status.COMPLETED
            else:
                new_submission.status = Submission.Status.IN_PROGRESS

            new_submission.save()

            if (
                new_submission.status == Submission.Status.COMPLETED
                and not was_completed
            ):
                send_submission_completed_sms(new_submission)

            return redirect("assignments:detail", pk=assignment.pk)
    else:
        form = SubmissionForm(instance=submission)

    return render(
        request,
        "assignments/assignment_detail_mentee.html",
        {
            "assignment": assignment,
            "submission": submission,
            "form": form,
        },
    )


@login_required
@mentor_required
def assignment_create(request):
    """멘토가 새 과제를 등록합니다."""

    if request.method == "POST":
        form = AssignmentForm(request.POST)

        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()

            send_new_assignment_sms(assignment)

            return redirect("assignments:detail", pk=assignment.pk)
    else:
        form = AssignmentForm()

    return render(
        request,
        "assignments/assignment_form.html",
        {
            "form": form,
            "form_title": "새 과제 등록",
        },
    )


@login_required
@mentor_required
def assignment_update(request, pk):
    """멘토가 기존 과제를 수정합니다."""

    assignment = get_object_or_404(Assignment, pk=pk)

    if request.method == "POST":
        form = AssignmentForm(
            request.POST,
            instance=assignment,
        )

        if form.is_valid():
            form.save()

            return redirect("assignments:detail", pk=assignment.pk)
    else:
        form = AssignmentForm(instance=assignment)

    return render(
        request,
        "assignments/assignment_form.html",
        {
            "form": form,
            "form_title": "과제 수정",
        },
    )


@login_required
@mentor_required
def assignment_delete(request, pk):
    """삭제 확인 후 과제를 삭제합니다."""

    assignment = get_object_or_404(Assignment, pk=pk)

    if request.method == "POST":
        assignment.delete()
        return redirect("assignments:list")

    return render(
        request,
        "assignments/assignment_confirm_delete.html",
        {
            "assignment": assignment,
        },
    )


@login_required
@mentee_required
def submission_delete(request, pk):
    """삭제 확인 후 자신의 제출물을 삭제합니다."""

    submission = get_object_or_404(
        Submission,
        assignment_id=pk,
        student=request.user,
    )

    if request.method == "POST":
        submission.delete()
        return redirect("assignments:detail", pk=pk)

    return render(
        request,
        "assignments/submission_confirm_delete.html",
        {
            "submission": submission,
        },
    )
