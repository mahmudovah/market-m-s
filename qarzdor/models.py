from django.db import models
from django.utils import timezone

from toifa.models import Product


class Debtor(models.Model):
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Qarzdor"
        verbose_name_plural = "Qarzdorlar"

    def __str__(self):
        return self.full_name


class Debt(models.Model):
    STATUS_OPEN = "OPEN"
    STATUS_CLOSED = "CLOSED"
    STATUS_OVERDUE = "OVERDUE"
    STATUSES = (
        (STATUS_OPEN, "Faol"),
        (STATUS_CLOSED, "Yopilgan"),
        (STATUS_OVERDUE, "Muddati o'tgan"),
    )

    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE, related_name="debts")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=14, decimal_places=2)
    issued_at = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUSES, default=STATUS_OPEN)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issued_at"]
        verbose_name = "Qarz"
        verbose_name_plural = "Qarzlar"

    def __str__(self):
        return f"{self.debtor.full_name} - {self.amount}"

    def refresh_status(self):
        today = timezone.localdate()
        if self.remaining_amount <= 0:
            self.status = self.STATUS_CLOSED
        elif self.due_date < today:
            self.status = self.STATUS_OVERDUE
        else:
            self.status = self.STATUS_OPEN


class DebtPayment(models.Model):
    TYPE_FULL = "TOLIQ"
    TYPE_PARTIAL = "QISMAN"
    PAYMENT_TYPES = (
        (TYPE_FULL, "To'liq"),
        (TYPE_PARTIAL, "Qisman"),
    )

    debt = models.ForeignKey(Debt, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES, default=TYPE_PARTIAL)
    paid_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_at"]
        verbose_name = "Qarz to'lovi"
        verbose_name_plural = "Qarz to'lovlari"

    def __str__(self):
        return f"{self.debt.debtor.full_name}: {self.amount}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            debt = self.debt
            debt.remaining_amount = max(0, debt.remaining_amount - self.amount)
            debt.refresh_status()
            debt.save(update_fields=["remaining_amount", "status"])

# Create your models here.
