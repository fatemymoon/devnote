"""과제 앱의 URL → 뷰 연결표. (config/urls.py에서 /assignments/ 아래로 포함됨)"""

from django.urls import path

from . import views


app_name = "assignments"

urlpatterns = [
    path("", views.assignment_list, name="list"),                  # 과제 목록 (전체)
    path("my/", views.assignment_workspace, name="workspace"),     # 내 작업 화면 (역할별)
    path("new/", views.assignment_create, name="create"),          # 과제 등록 (멘토)
    path("<int:pk>/", views.assignment_detail, name="detail"),     # 과제 상세 + 제출
    path("<int:pk>/edit/", views.assignment_update, name="update"),   # 과제 수정 (멘토)
    path("<int:pk>/delete/", views.assignment_delete, name="delete"), # 과제 삭제 (멘토)
    path(
        "<int:pk>/submission/delete/",   # pk번 과제에 대한 내 제출물 삭제 (학생)
        views.submission_delete,
        name="submission_delete",
    ),
]
