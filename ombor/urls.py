from django.urls import path

from . import views

urlpatterns = [
    path("", views.ombor_dashboard, name="ombor-dashboard"),
    path("stock/", views.stock_summary, name="ombor-stock"),
    path("movements/", views.movement_history, name="ombor-movements"),
    path("receipt-cost/", views.receipt_cost_report, name="ombor-receipt-cost"),
    path("export/stock.xlsx", views.export_stock_excel, name="export-ombor-excel"),
    path("export/stock.pdf", views.export_stock_pdf, name="export-ombor-pdf"),
]
