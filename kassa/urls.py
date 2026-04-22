from django.urls import path

from . import views

urlpatterns = [
    path("", views.kassa_dashboard, name="kassa-dashboard"),
    path("accounts/", views.account_balances, name="kassa-accounts"),
    path("monthly-compare/", views.monthly_compare, name="kassa-monthly-compare"),
]
