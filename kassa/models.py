from django.db import models


class CashAccount(models.Model):
    TYPE_SHOP = "DOKON"
    TYPE_PERSONAL = "SHAXSIY"
    ACCOUNT_TYPES = (
        (TYPE_SHOP, "Do'kon"),
        (TYPE_PERSONAL, "Shaxsiy"),
    )

    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["account_type", "name"]
        verbose_name = "Hisob"
        verbose_name_plural = "Hisoblar"

    def __str__(self):
        return f"{self.name} ({self.account_type})"


class CashTransaction(models.Model):
    DIR_IN = "KIRIM"
    DIR_OUT = "CHIQIM"
    DIRECTIONS = (
        (DIR_IN, "Kirim"),
        (DIR_OUT, "Chiqim"),
    )

    account = models.ForeignKey(CashAccount, on_delete=models.CASCADE, related_name="transactions")
    direction = models.CharField(max_length=10, choices=DIRECTIONS)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.CharField(max_length=100)
    source = models.CharField(max_length=120, blank=True)
    occurred_at = models.DateTimeField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name = "Kassa tranzaksiya"
        verbose_name_plural = "Kassa tranzaksiyalari"

    def __str__(self):
        return f"{self.account.name}: {self.direction} {self.amount}"


class CashTransfer(models.Model):
    from_account = models.ForeignKey(CashAccount, on_delete=models.PROTECT, related_name="out_transfers")
    to_account = models.ForeignKey(CashAccount, on_delete=models.PROTECT, related_name="in_transfers")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    occurred_at = models.DateTimeField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]
        verbose_name = "O'tkazma"
        verbose_name_plural = "O'tkazmalar"

    def __str__(self):
        return f"{self.from_account.name} -> {self.to_account.name}: {self.amount}"

# Create your models here.
