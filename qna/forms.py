"""질의응답(QnA) 앱의 입력 폼 정의.

- QuestionForm: 학생의 질문 작성/수정 폼
- AnswerForm: 멘토의 답변 작성/수정 폼
둘 다 내용(content) 한 필드만 입력받고, 작성자는 뷰에서 자동으로 채웁니다.
"""

from django import forms

from .models import Answer, Question


class QuestionForm(forms.ModelForm):
    """학생이 질문을 작성하고 수정할 때 사용하는 입력 양식입니다."""

    class Meta:
        model = Question

        fields = [
            "content",
        ]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 10,
                    "placeholder": "궁금한 내용을 입력하세요.",
                }
            ),
        }


class AnswerForm(forms.ModelForm):
    """멘토가 답변을 작성하고 수정할 때 사용하는 입력 양식입니다."""

    class Meta:
        model = Answer

        fields = [
            "content",
        ]

        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 10,
                    "placeholder": "답변 내용을 입력하세요.",
                }
            ),
        }
