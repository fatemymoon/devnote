"""질의응답(QnA) 앱의 화면 처리(뷰) 함수들.

접근 규칙:
- 학생: 본인 질문만 보고 쓰고 수정/삭제할 수 있음
- 멘토: 모든 질문을 보고 답변을 달 수 있음
"""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

# 역할 판별 도구는 assignments 앱의 것을 재사용
from assignments.decorators import is_mentor, mentee_required

from .forms import AnswerForm, QuestionForm
from .models import Question
from .notifications import send_new_answer_sms, send_new_question_sms


def _get_question_for(user, pk):
    """멘토는 모든 질문, 학생은 본인 질문만 가져옵니다.

    권한이 없는 질문에 접근하면 404를 발생시켜서
    남의 질문이 존재하는지조차 알 수 없게 합니다.
    """

    # select_related: 작성자 정보를 JOIN으로 한 번에 가져와 쿼리 수 절약
    questions = Question.objects.select_related("student")

    if not is_mentor(user):
        questions = questions.filter(student=user)

    question = questions.filter(pk=pk).first()

    if question is None:
        raise Http404

    return question


@login_required
def question_list(request):
    """질문 목록을 게시판 형태로 보여줍니다."""

    questions = Question.objects.select_related("answer", "student")

    # 학생은 본인 질문만 (멘토는 전체)
    if not is_mentor(request.user):
        questions = questions.filter(student=request.user)

    # 20개씩 페이지로 나눔
    paginator = Paginator(questions, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "qna/question_list.html",
        {
            "page_obj": page_obj,
        },
    )


@login_required
def question_detail(request, pk):
    """질문 내용과 답변을 보여줍니다. 멘토에게는 답변 폼이 보입니다."""

    question = _get_question_for(request.user, pk)

    # 답변이 아직 없으면 None (OneToOne이라 없을 때 예외가 나므로 getattr 사용)
    answer = getattr(question, "answer", None)

    # 학생: 질문과 답변만 보여주고 끝 (답변 폼 없음)
    if not is_mentor(request.user):
        return render(
            request,
            "qna/question_detail.html",
            {
                "question": question,
                "answer": answer,
            },
        )

    # ── 여기부터는 멘토 화면: 답변 작성/수정 처리 ──
    if request.method == "POST":
        # instance=answer: 기존 답변이 있으면 수정, 없으면(None) 새로 작성
        form = AnswerForm(
            request.POST,
            instance=answer,
        )

        if form.is_valid():
            # 처음 다는 답변인지 기억 (수정할 때는 문자를 다시 보내지 않기 위해)
            is_new_answer = answer is None

            new_answer = form.save(commit=False)
            new_answer.question = question
            new_answer.mentor = request.user
            new_answer.save()

            # 새 답변일 때만 질문 작성 학생에게 문자 알림
            if is_new_answer:
                send_new_answer_sms(new_answer)

            return redirect("qna:detail", pk=question.pk)
    else:
        form = AnswerForm(instance=answer)

    return render(
        request,
        "qna/question_detail.html",
        {
            "question": question,
            "answer": answer,
            "answer_form": form,
        },
    )


@login_required
@mentee_required  # 학생만 질문을 쓸 수 있음
def question_create(request):
    """학생이 새 질문을 등록합니다."""

    if request.method == "POST":
        form = QuestionForm(request.POST)

        if form.is_valid():
            # 작성자를 현재 로그인한 학생으로 지정한 뒤 저장
            question = form.save(commit=False)
            question.student = request.user
            question.save()

            # 모든 멘토에게 새 질문 알림 문자 발송
            send_new_question_sms(question)

            return redirect("qna:detail", pk=question.pk)
    else:
        form = QuestionForm()

    return render(
        request,
        "qna/question_form.html",
        {
            "form": form,
            "form_title": "새 질문 작성",
        },
    )


@login_required
@mentee_required
def question_update(request, pk):
    """학생이 본인 질문을 수정합니다."""

    # student=request.user 조건 때문에 남의 질문은 404
    question = get_object_or_404(
        Question,
        pk=pk,
        student=request.user,
    )

    if request.method == "POST":
        form = QuestionForm(
            request.POST,
            instance=question,
        )

        if form.is_valid():
            form.save()

            return redirect("qna:detail", pk=question.pk)
    else:
        form = QuestionForm(instance=question)

    return render(
        request,
        "qna/question_form.html",
        {
            "form": form,
            "form_title": "질문 수정",
        },
    )


@login_required
@mentee_required
def question_delete(request, pk):
    """삭제 확인 후 학생이 본인 질문을 삭제합니다."""

    question = get_object_or_404(
        Question,
        pk=pk,
        student=request.user,
    )

    if request.method == "POST":
        question.delete()
        return redirect("qna:list")

    return render(
        request,
        "qna/question_confirm_delete.html",
        {
            "question": question,
        },
    )
