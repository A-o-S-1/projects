from django.urls import path

from . import views

app_name = "results"

urlpatterns = [
    path("check-result/", views.ResultLookupView.as_view(), name="check"),
    path("check-result/view/", views.ResultDetailView.as_view(), name="view_result"),
    path("check-result/done/", views.ResultLogoutView.as_view(), name="done"),
    path("staff/upload-scores/", views.ScoreUploadView.as_view(), name="upload_scores"),
    path("staff/upload-workbook/", views.WorkbookUploadView.as_view(), name="upload_workbook"),
    path("staff/master-sheet/", views.MasterSheetView.as_view(), name="master_sheet"),
    path("staff/result/<int:student_id>/<int:term_id>/", views.StaffResultPrintView.as_view(), name="staff_result_print"),
    path("staff/class-results/", views.StaffClassResultsPrintView.as_view(), name="staff_class_results_print"),
]
