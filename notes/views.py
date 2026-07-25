"""개발노트 앱의 화면 처리(뷰) 함수들.

요청(request)을 받아 DB를 조회/수정하고, 템플릿을 렌더링해 응답을 만듭니다.
모든 뷰에 @login_required가 붙어 있어 로그인해야만 접근할 수 있고,
조회 시 항상 author=request.user 조건을 걸어 본인 노트만 다룹니다.
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Q  # 여러 조건을 OR(|)로 묶을 때 사용
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NoteForm
from .models import Note


@login_required
def note_list(request):
    """현재 사용자의 노트를 검색하고 카테고리별로 보여줍니다."""

    # 기본: 내가 쓴 노트 전부
    notes = Note.objects.filter(author=request.user)

    # URL 쿼리스트링에서 검색어(?q=...)와 카테고리(?category=...)를 읽음
    search_query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()

    # 검색어가 있으면 제목/내용/카테고리/태그 중 하나라도 포함된 노트만 남김
    # (icontains = 대소문자 구분 없이 부분 일치)
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
            | Q(category__icontains=search_query)
            | Q(tags__icontains=search_query)
        )

    # 카테고리를 선택했으면 해당 카테고리만 남김
    if selected_category:
        notes = notes.filter(category=selected_category)

    # 필터 버튼용: 내 노트에 존재하는 카테고리 목록 (중복 제거, 가나다순)
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

    # pk에 해당하는 내 노트를 찾고, 없으면(남의 노트 포함) 404 에러
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
    """새로운 개발노트를 작성합니다.

    GET 요청이면 빈 폼을 보여주고, POST 요청이면 입력값을 검증 후 저장합니다.
    """

    if request.method == "POST":
        form = NoteForm(request.POST)

        if form.is_valid():
            # commit=False: DB에 바로 저장하지 않고 객체만 먼저 받음
            # (폼에 없는 author 필드를 채운 뒤 저장해야 하기 때문)
            note = form.save(commit=False)
            note.author = request.user
            note.save()

            # 저장 후 방금 만든 노트의 상세 페이지로 이동
            return redirect(
                "notes:detail",
                pk=note.pk,
            )
    else:
        form = NoteForm()  # 처음 들어왔을 때 보여줄 빈 폼

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
        # instance=note: 새로 만들지 않고 기존 노트를 수정 대상으로 지정
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
    """삭제 확인 후 개발노트를 삭제합니다.

    GET이면 "정말 삭제할까요?" 확인 페이지를 보여주고,
    확인 버튼을 눌러 POST가 오면 실제로 삭제합니다.
    """

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