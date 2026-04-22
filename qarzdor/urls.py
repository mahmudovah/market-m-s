from django.urls import path

from . import views

urlpatterns = [
    path("", views.qarzdor_dashboard, name="qarzdor-dashboard"),
    path("debts/", views.debt_list, name="debt-list"),
    path("reminders/", views.reminders, name="debt-reminders"),
    path("export/debts.xlsx", views.export_debt_excel, name="export-qarzdor-excel"),
    path("export/debts.pdf", views.export_debt_pdf, name="export-qarzdor-pdf"),
]
