from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NoteForm
from .models import Note


@login_required
def note_list(request):
    """현재 사용자의 노트를 검색하고 카테고리별로 보여줍니다."""

    notes = Note.objects.filter(author=request.user)

    search_query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()

    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
            | Q(category__icontains=search_query)
            | Q(tags__icontains=search_query)
        )

    if selected_category:
        notes = notes.filter(category=selected_category)

    categories = (
        Note.objects.filter(author=request.user)
        .exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    return render(
        request,
        "notes/note_list.html",
        {
            "notes": notes,
            "search_query": search_query,
            "selected_category": selected_category,
            "categories": categories,
        },
    )

@login_required
def note_detail(request, pk):
    """선택한 개발노트의 전체 내용을 보여줍니다."""

    note = get_object_or_404(
        Note,
        pk=pk,
        author=request.user,
    )

    return render(
        request,
        "notes/note_detail.html",
        {
            "note": note,
        },
    )


@login_required
def note_create(request):
    """새로운 개발노트를 작성합니다."""

    if request.method == "POST":
        form = NoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)
            note.author = request.user
            note.save()

            return redirect(
                "notes:detail",
                pk=note.pk,
            )
    else:
        form = NoteForm()

    return render(
        request,
        "notes/note_form.html",
        {
            "form": form,
            "form_title": "새 개발노트 작성",
        },
    )


@login_required
def note_update(request, pk):
    """기존 개발노트를 수정합니다."""

    note = get_object_or_404(
        Note,
        pk=pk,
        author=request.user,
    )

    if request.method == "POST":
        form = NoteForm(
            request.POST,
            instance=note,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "notes:detail",
                pk=note.pk,
            )
    else:
        form = NoteForm(instance=note)

    return render(
        request,
        "notes/note_form.html",
        {
            "form": form,
            "form_title": "개발노트 수정",
        },
    )


@login_required
def note_delete(request, pk):
    """삭제 확인 후 개발노트를 삭제합니다."""

    note = get_object_or_404(
        Note,
        pk=pk,
        author=request.user,
    )

    if request.method == "POST":
        note.delete()
        return redirect("notes:list")

    return render(
        request,
        "notes/note_confirm_delete.html",
        {
            "note": note,
        },
    )