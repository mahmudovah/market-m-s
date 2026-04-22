from django.conf import settings
from django.db import models
from django.utils import timezone


class ShopProfile(models.Model):
    shop_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    currency = models.CharField(max_length=10, default="UZS")
    language = models.CharField(max_length=10, default="uz")
    notification_phone = models.CharField(max_length=30, blank=True)
    low_stock_alert_limit = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Do'kon profili"
        verbose_name_plural = "Do'kon profillari"

    def __str__(self):
        return self.shop_name


class SecuritySetting(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="security_setting"
    )
    pin_code = models.CharField(max_length=8)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Xavfsizlik sozlamasi"
        verbose_name_plural = "Xavfsizlik sozlamalari"

    def __str__(self):
        return f"{self.user.username} PIN"


class ExportLog(models.Model):
    TYPE_EXCEL = "EXCEL"
    TYPE_PDF = "PDF"
    FILE_TYPES = (
        (TYPE_EXCEL, "Excel"),
        (TYPE_PDF, "PDF"),
    )

    module = models.CharField(max_length=50)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Eksport log"
        verbose_name_plural = "Eksport loglari"

    def __str__(self):
        return f"{self.module} - {self.file_type}"

# Create your models here.
