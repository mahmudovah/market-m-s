from django.contrib import admin

from .models import StockMovement, WarehouseReceipt, WarehouseReceiptItem


class WarehouseReceiptItemInline(admin.TabularInline):
    model = WarehouseReceiptItem
    extra = 1


@admin.register(WarehouseReceipt)
class WarehouseReceiptAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier_name", "received_at", "created_at")
    list_filter = ("received_at",)
    search_fields = ("supplier_name", "note")
    inlines = (WarehouseReceiptItemInline,)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "movement_type", "quantity", "unit_price", "moved_at", "source")
    list_filter = ("movement_type", "moved_at")
    search_fields = ("product__name", "source", "note")

# Register your models here.
