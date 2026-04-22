from django.db.models import Count
from django.http import JsonResponse

from .models import Category, Product, ProductPriceHistory


def category_list(request):
    categories = Category.objects.annotate(product_count=Count("products")).values(
        "id", "name", "order", "product_count"
    )
    return JsonResponse({"results": list(categories)})


def product_list(request):
    products = Product.objects.select_related("category").values(
        "id",
        "name",
        "category__name",
        "unit",
        "sale_price",
        "min_stock_limit",
        "image_url",
        "is_active",
    )
    return JsonResponse({"results": list(products)})


def price_history_list(request):
    history = ProductPriceHistory.objects.select_related("product").values(
        "id",
        "product__name",
        "old_price",
        "new_price",
        "changed_at",
        "note",
    )[:100]
    return JsonResponse({"results": list(history)})

# Create your views here.
