"""개발노트 입력 폼 정의.

ModelForm은 모델(Note)의 필드 정의를 바탕으로
HTML 입력 폼 생성 + 입력값 검증 + 저장까지 처리해 줍니다.
"""

from django import forms

from .models import Note


class NoteForm(forms.ModelForm):
    """개발노트를 작성하고 수정할 때 사용하는 입력 양식입니다."""

    class Meta:
        model = Note  # 이 폼이 다루는 모델

        # 사용자에게 입력받을 필드 (author, 작성일 등은 뷰에서 자동 처리)
        fields = [
            "title",
            "content",
            "category",
            "tags",
            "is_pinned",
        ]

        # 각 필드의 HTML 표현 방식과 placeholder(입력 안내 문구) 지정
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "노트 제목을 입력하세요.",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "rows": 15,
                    "placeholder": "배운 내용이나 명령어를 입력하세요.",
                }
            ),
            "category": forms.TextInput(
                attrs={
                    "placeholder": "예: Django, Linux, Docker",
                }
            ),
            "tags": forms.TextInput(
                attrs={
                    "placeholder": "예: Python, 서버, 설치",
                }
            ),
        }