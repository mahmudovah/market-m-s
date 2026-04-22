from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "sold_at",
        "operator",
        "cash_account",
        "total_amount",
        "total_cost",
        "profit_amount",
        "is_finalized",
    )
    list_filter = ("is_finalized", "sold_at")
    search_fields = ("customer_name", "note")
    inlines = (SaleItemInline,)

# Register your models here.
