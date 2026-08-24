from django.urls import path

from . import views

app_name = "results"

urlpatterns = [
    path("check-result/", views.ResultLookupView.as_view(), name="check"),
    path("check-result/view/", views.ResultDetailView.as_view(), name="view_result"),
    path("check-result/done/", views.ResultLogoutView.as_view(), name="done"),
]
