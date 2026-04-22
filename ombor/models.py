from django.db import models
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from uuid import uuid4

from toifa.models import Product


class WarehouseReceipt(models.Model):
    receipt_code = models.CharField(max_length=40, blank=True, db_index=True)
    qr_payload = models.CharField(max_length=255, blank=True)
    supplier_name = models.CharField(max_length=150, blank=True)
    received_at = models.DateTimeField()
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="warehouse_receipts"
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Yuk qabuli"
        verbose_name_plural = "Yuk qabullari"

    def __str__(self):
        return f"{self.receipt_code or 'Qabul'} ({self.received_at:%Y-%m-%d})"

    def save(self, *args, **kwargs):
        if not self.receipt_code:
            self.receipt_code = f"YQ-{timezone.now():%Y%m%d%H%M%S}-{uuid4().hex[:4].upper()}"
        if not self.qr_payload:
            self.qr_payload = self.receipt_code
        super().save(*args, **kwargs)


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
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="stock_movements"
    )
    source = models.CharField(max_length=100, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-moved_at"]
        verbose_name = "Harakat"
        verbose_name_plural = "Harakatlar tarixi"

    def __str__(self):
        return f"{self.product.name} {self.movement_type} {self.quantity}"

    @classmethod
    def current_stock(cls, product, exclude_movement_id=None):
        qty_field = DecimalField(max_digits=14, decimal_places=3)
        qty_zero = Value(0, output_field=qty_field)
        base = cls.objects.filter(product=product)
        if exclude_movement_id:
            base = base.exclude(pk=exclude_movement_id)
        agg = base.aggregate(
            kirim=Coalesce(
                Sum("quantity", filter=Q(movement_type=cls.TYPE_IN), output_field=qty_field),
                qty_zero,
                output_field=qty_field,
            ),
            chiqim=Coalesce(
                Sum("quantity", filter=Q(movement_type=cls.TYPE_OUT), output_field=qty_field),
                qty_zero,
                output_field=qty_field,
            ),
        )
        return agg["kirim"] - agg["chiqim"]

    def clean(self):
        super().clean()
        if self.movement_type == self.TYPE_OUT:
            available = self.current_stock(self.product, exclude_movement_id=self.pk)
            if self.quantity > available:
                raise ValidationError(
                    {"quantity": f"Hozir faqat {available} ta mavjud. {self.quantity} ta ayirib bo'lmaydi."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# Create your models here.
