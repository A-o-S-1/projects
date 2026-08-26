from django.urls import path

from . import views

app_name = "results"

urlpatterns = [

    path("staff/upload-scores/", views.ScoreUploadView.as_view(), name="upload_scores"),

    path("staff/master-sheet/", views.MasterSheetView.as_view(), name="master_sheet"),

    path("check-result/", views.ResultLookupView.as_view(), name="check"),

    path("check-result/view/", views.ResultDetailView.as_view(), name="view_result"),

    path("check-result/done/", views.ResultLogoutView.as_view(), name="done"),

]