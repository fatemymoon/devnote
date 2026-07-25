from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import is_mentor, mentee_required, mentor_required
from .sms import send_new_assignment_sms, send_submission_completed_sms
from .forms import AssignmentForm, SubmissionForm
from .models import Assignment, Submission


@login_required
def assignment_list(request):
    """전체 과제를 게시판 형태로 보여줍니다. 멘토/멘티 모두 접근할 수 있습니다."""

    assignments = Assignment.objects.all()

    search_query = request.GET.get("q", "").strip()

    if search_query:
        assignments = assignments.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    paginator = Paginator(assignments, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    submissions = Submission.objects.filter(
        assignment__in=page_obj.object_list,
    )

    if not is_mentor(request.user):
        submissions = submissions.filter(student=request.user)

    status_map = {
        submission.assignment_id: submission
        for submission in submissions
    }

    rows = [
        {
            "assignment": assignment,
            "submission": status_map.get(assignment.pk),
        }
        for assignment in page_obj.object_list
    ]

    return render(
        request,
        "assignments/assignment_list.html",
        {
            "rows": rows,
            "page_obj": page_obj,
            "search_query": search_query,
        },
    )


@login_required
def assignment_workspace(request):
    """역할별 개인 작업 화면입니다. 멘토는 과제출제, 멘티는 과제제출."""

    if is_mentor(request.user):
        assignments = (
            Assignment.objects.filter(created_by=request.user)
            .annotate(
                submission_count=Count("submissions"),
                completed_count=Count(
                    "submissions",
                    filter=Q(submissions__status=Submission.Status.COMPLETED),
                ),
            )
            .prefetch_related("submissions__student")
        )

        return render(
            request,
            "assignments/assignment_workspace_mentor.html",
            {
                "assignments": assignments,
            },
        )

    my_submissions = {
        submission.assignment_id: submission
        for submission in Submission.objects.filter(student=request.user)
    }

    def sort_rank(assignment):
        submission = my_submissions.get(assignment.pk)

        if submission is None:
            return 0

        if submission.status == Submission.Status.IN_PROGRESS:
            return 1

        return 2

    rows = [
        {
            "assignment": assignment,
            "submission": my_submissions.get(assignment.pk),
        }
        for assignment in sorted(
            Assignment.objects.all(),
            key=lambda a: (sort_rank(a), -a.created_at.timestamp()),
        )
    ]

    return render(
        request,
        "assignments/assignment_workspace_mentee.html",
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
