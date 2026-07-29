"""질의응답 앱의 URL → 뷰 연결표. (config/urls.py에서 /qna/ 아래로 포함됨)"""

from django.urls import path

from . import views


app_name = "qna"

urlpatterns = [
    path("", views.question_list, name="list"),                    # 질문 목록
    path("new/", views.question_create, name="create"),            # 질문 작성 (학생)
    path("<int:pk>/", views.question_detail, name="detail"),       # 질문 상세 + 답변 (멘토)
    path("<int:pk>/edit/", views.question_update, name="update"),  # 질문 수정 (학생)
    path("<int:pk>/delete/", views.question_delete, name="delete"),# 질문 삭제 (학생)
]
