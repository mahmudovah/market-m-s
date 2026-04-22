from django.contrib import admin

from .models import Category, Product, ProductPriceHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "created_at")
    search_fields = ("name",)
    ordering = ("order", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "sale_price", "min_stock_limit", "is_active")
    list_filter = ("category", "unit", "is_active")
    search_fields = ("name", "category__name")


@admin.register(ProductPriceHistory)
class ProductPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("product", "old_price", "new_price", "changed_at")
    list_filter = ("changed_at",)
    search_fields = ("product__name",)

# Register your models here.
