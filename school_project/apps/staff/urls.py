from django.urls import path

from . import views

app_name = "staff"

urlpatterns = [
    path("staff/", views.StaffDirectoryView.as_view(), name="directory"),
    path("management/", views.ManagementView.as_view(), name="management"),
]
