from django.db import models

from toifa.models import Product


class WarehouseReceipt(models.Model):
    supplier_name = models.CharField(max_length=150, blank=True)
    received_at = models.DateTimeField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Yuk qabuli"
        verbose_name_plural = "Yuk qabullari"

    def __str__(self):
        return f"Qabul #{self.pk} ({self.received_at:%Y-%m-%d})"


class WarehouseReceiptItem(models.Model):
    receipt = models.ForeignKey(WarehouseReceipt, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="receipt_items")
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Qabul elementi"
        verbose_name_plural = "Qabul elementlari"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class StockMovement(models.Model):
    TYPE_IN = "KIRIM"
    TYPE_OUT = "CHIQIM"
    TYPE_ADJUST = "TUZATISH"
    MOVEMENT_TYPES = (
        (TYPE_IN, "Kirim"),
        (TYPE_OUT, "Chiqim"),
        (TYPE_ADJUST, "Tuzatish"),
    )

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    moved_at = models.DateTimeField()
    source = models.CharField(max_length=100, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-moved_at"]
        verbose_name = "Harakat"
        verbose_name_plural = "Harakatlar tarixi"

    def __str__(self):
        return f"{self.product.name} {self.movement_type} {self.quantity}"

# Create your models here.
