from django.urls import path

from . import views


app_name = "assignments"

urlpatterns = [
    path("", views.assignment_list, name="list"),
    path("my/", views.assignment_workspace, name="workspace"),
    path("new/", views.assignment_create, name="create"),
    path("<int:pk>/", views.assignment_detail, name="detail"),
    path("<int:pk>/edit/", views.assignment_update, name="update"),
    path("<int:pk>/delete/", views.assignment_delete, name="delete"),
    path(
        "<int:pk>/submission/delete/",
        views.submission_delete,
        name="submission_delete",
    ),
]
