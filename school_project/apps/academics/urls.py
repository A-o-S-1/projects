from django.urls import path

from . import views

app_name = "academics"

urlpatterns = [
    path("academics/", views.AcademicsView.as_view(), name="academics"),
]
