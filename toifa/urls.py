from django.urls import path

from . import views

urlpatterns = [
    path("", views.category_list, name="toifa-list"),
    path("products/", views.product_list, name="product-list"),
    path("price-history/", views.price_history_list, name="price-history-list"),
]
