from decimal import Decimal

from django.db import models, transaction
from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.conf import settings

from kassa.models import CashAccount, CashTransaction
from ombor.models import StockMovement, WarehouseReceiptItem
from toifa.models import Product


def latest_product_cost(product: Product) -> Decimal:
    receipt_item = (
        WarehouseReceiptItem.objects.filter(product=product).select_related("receipt").order_by("-receipt__received_at").first()
    )
    if receipt_item:
        return receipt_item.unit_cost

    stock_in = (
        StockMovement.objects.filter(product=product, movement_type=StockMovement.TYPE_IN)
        .order_by("-moved_at")
        .first()
    )
    if stock_in and stock_in.unit_price:
        return stock_in.unit_price
    return product.sale_price


class Sale(models.Model):
    customer_name = models.CharField(max_length=150, blank=True)
    note = models.CharField(max_length=255, blank=True)
    sold_at = models.DateTimeField(default=timezone.now)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="sales"
    )
    cash_account = models.ForeignKey(
        CashAccount, on_delete=models.PROTECT, related_name="sales", null=True, blank=True
    )
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    profit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sold_at"]
        verbose_name = "Sotuv"
        verbose_name_plural = "Sotuvlar"

    def __str__(self):
        return f"Sotuv #{self.pk} - {self.total_amount}"

    @transaction.atomic
    def finalize(self):
        if self.is_finalized:
            return

        items = list(self.items.select_related("product"))
        total_amount = Decimal("0")
        total_cost = Decimal("0")
        for item in items:
            line_amount = item.quantity * item.unit_price
            line_cost = item.quantity * item.purchase_price_at_sale
            total_amount += line_amount
            total_cost += line_cost

            StockMovement.objects.create(
                product=item.product,
                movement_type=StockMovement.TYPE_OUT,
                quantity=item.quantity,
                unit_price=item.unit_price,
                moved_at=self.sold_at,
                operator=self.operator,
                source="POS sotuv",
                note=f"Sotuv #{self.pk}",
            )

        self.total_amount = total_amount
        self.total_cost = total_cost
        self.profit_amount = total_amount - total_cost
        self.is_finalized = True
        self.finalized_at = timezone.now()
        self.save(
            update_fields=["total_amount", "total_cost", "profit_amount", "is_finalized", "finalized_at"]
        )

        if self.cash_account and self.total_amount > 0:
            CashTransaction.objects.create(
                account=self.cash_account,
                direction=CashTransaction.DIR_IN,
                amount=self.total_amount,
                category="POS sotuv",
                source=f"Sotuv #{self.pk}",
                occurred_at=self.sold_at,
                note=self.note,
            )

    def refresh_totals(self):
        money_field = models.DecimalField(max_digits=14, decimal_places=2)
        money_zero = Value(0, output_field=money_field)
        totals = self.items.aggregate(
            total_amount=Coalesce(
                Sum(F("quantity") * F("unit_price"), output_field=money_field),
                money_zero,
                output_field=money_field,
            ),
            total_cost=Coalesce(
                Sum(F("quantity") * F("purchase_price_at_sale"), output_field=money_field),
                money_zero,
                output_field=money_field,
            ),
        )
        self.total_amount = totals["total_amount"]
        self.total_cost = totals["total_cost"]
        self.profit_amount = self.total_amount - self.total_cost
        self.save(update_fields=["total_amount", "total_cost", "profit_amount"])


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    purchase_price_at_sale = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sotuv elementi"
        verbose_name_plural = "Sotuv elementlari"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        if not self.purchase_price_at_sale:
            self.purchase_price_at_sale = latest_product_cost(self.product)
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

# Create your models here.
