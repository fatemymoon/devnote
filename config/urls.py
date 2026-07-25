"""프로젝트 전체 URL 설정.

들어온 주소(URL)를 보고 어떤 앱/뷰로 연결할지 결정하는 최상위 라우터입니다.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views  # Django 기본 제공 로그인/로그아웃 뷰
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    # 루트 주소(/)로 오면 과제 목록으로 이동시킵니다.
    # permanent=False → 302 임시 리다이렉트 (나중에 홈 화면을 바꿔도 브라우저 캐시 영향 없음)
    path(
        "",
        RedirectView.as_view(
            url="/assignments/",
            permanent=False,
        ),
        name="home",
    ),

    # 로그인 페이지: Django 기본 LoginView에 우리가 만든 템플릿만 지정
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
        ),
        name="login",
    ),

    # 로그아웃: 처리 후 settings의 LOGOUT_REDIRECT_URL(login)로 이동
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path("admin/", admin.site.urls),                     # 관리자 페이지
    path("notes/", include("notes.urls")),               # 개발노트 앱
    path("assignments/", include("assignments.urls")),   # 과제 앱
    path("qna/", include("qna.urls")),                   # 질의응답 앱
]

# 개발 모드(DEBUG=True)일 때만 업로드 파일(media)을 Django가 직접 서빙합니다.
# 운영 환경에서는 웹서버(nginx 등)가 이 역할을 담당해야 합니다.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )