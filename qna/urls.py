from django.urls import path

from . import views


app_name = "qna"

urlpatterns = [
    path("", views.question_list, name="list"),
    path("new/", views.question_create, name="create"),
    path("<int:pk>/", views.question_detail, name="detail"),
    path("<int:pk>/edit/", views.question_update, name="update"),
    path("<int:pk>/delete/", views.question_delete, name="delete"),
]
