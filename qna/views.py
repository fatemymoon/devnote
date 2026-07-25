from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from assignments.decorators import is_mentor, mentee_required

from .forms import AnswerForm, QuestionForm
from .models import Question
from .notifications import send_new_answer_sms, send_new_question_sms


def _get_question_for(user, pk):
    """멘토는 모든 질문, 학생은 본인 질문만 가져옵니다."""

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

    if not is_mentor(request.user):
        questions = questions.filter(student=request.user)

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

    answer = getattr(question, "answer", None)

    if not is_mentor(request.user):
        return render(
            request,
            "qna/question_detail.html",
            {
                "question": question,
                "answer": answer,
            },
        )

    if request.method == "POST":
        form = AnswerForm(
            request.POST,
            instance=answer,
        )

        if form.is_valid():
            is_new_answer = answer is None

            new_answer = form.save(commit=False)
            new_answer.question = question
            new_answer.mentor = request.user
            new_answer.save()

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
@mentee_required
def question_create(request):
    """학생이 새 질문을 등록합니다."""

    if request.method == "POST":
        form = QuestionForm(request.POST)

        if form.is_valid():
            question = form.save(commit=False)
            question.student = request.user
            question.save()

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
