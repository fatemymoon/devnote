from django.urls import path

from . import views


app_name = "notes"

urlpatterns = [
    path("", views.note_list, name="list"),
    path("new/", views.note_create, name="create"),
    path("<int:pk>/", views.note_detail, name="detail"),
    path("<int:pk>/edit/", views.note_update, name="update"),
    path("<int:pk>/delete/", views.note_delete, name="delete"),
]