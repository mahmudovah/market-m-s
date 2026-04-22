from django.urls import path

from . import views

urlpatterns = [
    path("", views.ombor_dashboard, name="ombor-dashboard"),
    path("stock/", views.stock_summary, name="ombor-stock"),
    path("movements/", views.movement_history, name="ombor-movements"),
    path("receipt-cost/", views.receipt_cost_report, name="ombor-receipt-cost"),
]
