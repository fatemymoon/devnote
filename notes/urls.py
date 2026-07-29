"""개발노트 앱의 URL → 뷰 연결표. (config/urls.py에서 /notes/ 아래로 포함됨)"""

from django.urls import path

from . import views


# 템플릿에서 {% url "notes:list" %}처럼 앱 이름을 붙여 참조하기 위한 네임스페이스
app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),                    # /notes/ → 노트 목록
    path("new/", views.note_create, name="create"),            # /notes/new/ → 새 노트 작성
    path("<int:pk>/", views.note_detail, name="detail"),       # /notes/3/ → 3번 노트 상세
    path("<int:pk>/edit/", views.note_update, name="update"),  # /notes/3/edit/ → 수정
    path("<int:pk>/delete/", views.note_delete, name="delete"),# /notes/3/delete/ → 삭제
]