from django.urls import path

from .views import (
    dashboard_detail_view,
    dashboard_view,
    timecard_pdf_view,
    timecard_print_preview_view,
    timecard_view,
)

app_name = "timecard"

urlpatterns = [
    path("", timecard_view, name="timecard"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("dashboard/<int:pk>/", dashboard_detail_view, name="dashboard-detail"),
    path("dashboard/<int:pk>/print-preview/", timecard_print_preview_view, name="timecard-print-preview"),
    path("dashboard/<int:pk>/pdf/", timecard_pdf_view, name="timecard-pdf"),
]
