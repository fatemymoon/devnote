"""과제 앱의 입력 폼 정의.

- AssignmentForm: 멘토의 과제 등록/수정 폼
- SubmissionForm: 학생의 과제 제출 폼 (첨부파일 포함)
"""

from django import forms

from .models import Assignment, Submission


class AssignmentForm(forms.ModelForm):
    """멘토가 과제를 등록하고 수정할 때 사용하는 입력 양식입니다."""

    class Meta:
        model = Assignment

        fields = [
            "title",
            "description",
            "due_date",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "과제 제목을 입력하세요.",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 12,
                    "placeholder": "과제 내용을 입력하세요.",
                }
            ),
            # type="date" → 브라우저 기본 달력 선택 UI 사용
            "due_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }


class SubmissionForm(forms.ModelForm):
    """학생이 과제 수행 결과를 제출할 때 사용하는 입력 양식입니다."""

    class Meta:
        model = Submission

        fields = [
            "content",
            "attachment",
        ]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 12,
                    "placeholder": "수행한 내용을 입력하세요.",
                }
            ),
        }
