from django.urls import path

from . import views

urlpatterns = [
    path("pos/", views.pos_page, name="web-pos"),
    path("receipt/<int:sale_id>/", views.sale_receipt, name="sale-receipt"),
    path("profit/", views.profit_report, name="web-profit"),
    path("export/sales.xlsx", views.export_sales_excel, name="export-sales-excel"),
    path("export/sales.pdf", views.export_sales_pdf, name="export-sales-pdf"),
]

