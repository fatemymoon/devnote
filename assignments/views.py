"""과제 앱의 화면 처리(뷰) 함수들.

역할에 따라 다르게 동작합니다:
- 멘토: 과제 등록/수정/삭제, 학생들의 제출 현황 확인
- 멘티(학생): 과제 확인, 수행 결과 제출
"""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator  # 목록을 페이지 단위로 나누기
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

    # 검색어(?q=...)가 있으면 제목/설명에서 검색
    search_query = request.GET.get("q", "").strip()

    if search_query:
        assignments = assignments.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    # 20개씩 페이지를 나누고, ?page= 값에 해당하는 페이지를 가져옴
    paginator = Paginator(assignments, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    # 현재 페이지 과제들의 제출물을 한 번의 쿼리로 미리 가져옴 (N+1 쿼리 방지)
    submissions = Submission.objects.filter(
        assignment__in=page_obj.object_list,
    )

    # 학생은 자기 제출물만 볼 수 있음 (멘토는 전체)
    if not is_mentor(request.user):
        submissions = submissions.filter(student=request.user)

    # {과제 id: 제출물} 사전으로 만들어 과제별 제출 상태를 빠르게 찾음
    status_map = {
        submission.assignment_id: submission
        for submission in submissions
    }

    # 템플릿에서 쓰기 좋게 (과제, 제출물) 쌍의 목록으로 구성
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
        # 멘토: 내가 낸 과제 목록 + 과제별 제출/완료 수를 DB에서 함께 계산(annotate)
        assignments = (
            Assignment.objects.filter(created_by=request.user)
            .annotate(
                submission_count=Count("submissions"),  # 전체 제출 수
                completed_count=Count(                  # "완료" 상태인 제출 수만 집계
                    "submissions",
                    filter=Q(submissions__status=Submission.Status.COMPLETED),
                ),
            )
            # 제출 학생 정보를 미리 불러와 템플릿에서 추가 쿼리가 안 나가게 함
            .prefetch_related("submissions__student")
        )

        return render(
            request,
            "assignments/assignment_workspace_mentor.html",
            {
                "assignments": assignments,
            },
        )

    # 멘티: 내 제출물을 {과제 id: 제출물} 사전으로 준비
    my_submissions = {
        submission.assignment_id: submission
        for submission in Submission.objects.filter(student=request.user)
    }

    def sort_rank(assignment):
        """과제 정렬 우선순위: 미제출(0) → 진행중(1) → 완료(2) 순으로 위에 표시."""
        submission = my_submissions.get(assignment.pk)

        if submission is None:
            return 0

        if submission.status == Submission.Status.IN_PROGRESS:
            return 1

        return 2

    # 우선순위가 같으면 최신 과제가 먼저 오도록 정렬
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

    # 멘토에게는 이 과제의 전체 제출 현황을 보여주고 끝
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

    # ── 여기부터는 학생(멘티) 화면 ──
    # 이 과제에 대한 내 기존 제출물 (없으면 None → 새로 작성)
    submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user,
    ).first()

    if request.method == "POST":
        # request.FILES: 첨부파일 업로드 처리용
        form = SubmissionForm(
            request.POST,
            request.FILES,
            instance=submission,
        )

        if form.is_valid():
            # 저장 전에 이미 "완료" 상태였는지 기억해 둠 (문자 중복 발송 방지용)
            was_completed = (
                submission is not None
                and submission.status == Submission.Status.COMPLETED
            )

            new_submission = form.save(commit=False)
            new_submission.assignment = assignment
            new_submission.student = request.user

            # 어떤 버튼을 눌렀는지에 따라 상태 결정
            # "완료 제출" 버튼 → 완료 / "임시 저장" 버튼 → 진행중
            if request.POST.get("action") == "complete":
                new_submission.status = Submission.Status.COMPLETED
            else:
                new_submission.status = Submission.Status.IN_PROGRESS

            new_submission.save()

            # 이번에 처음으로 완료 상태가 됐을 때만 멘토에게 문자 알림
            if (
                new_submission.status == Submission.Status.COMPLETED
                and not was_completed
            ):
                send_submission_completed_sms(new_submission)

            return redirect("assignments:detail", pk=assignment.pk)
    else:
        # GET 요청: 기존 제출물이 있으면 그 내용이 채워진 폼을 보여줌
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
@mentor_required  # 멘토만 접근 가능 (학생이 접근하면 403 에러)
def assignment_create(request):
    """멘토가 새 과제를 등록합니다."""

    if request.method == "POST":
        form = AssignmentForm(request.POST)

        if form.is_valid():
            # 출제자를 현재 로그인한 멘토로 지정한 뒤 저장
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()

            # 모든 학생에게 새 과제 알림 문자 발송
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
@mentee_required  # 학생만 접근 가능
def submission_delete(request, pk):
    """삭제 확인 후 자신의 제출물을 삭제합니다."""

    # pk는 과제 번호. 그 과제에 대한 "내" 제출물만 찾음 (남의 것은 404)
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
