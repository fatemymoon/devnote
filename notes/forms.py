from django import forms

from .models import Note


class NoteForm(forms.ModelForm):
    """개발노트를 작성하고 수정할 때 사용하는 입력 양식입니다."""

    class Meta:
        model = Note

        fields = [
            "title",
            "content",
            "category",
            "tags",
            "is_pinned",
        ]

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