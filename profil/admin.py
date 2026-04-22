from django.contrib import admin

from .models import ExportLog, SecuritySetting, ShopProfile


@admin.register(ShopProfile)
class ShopProfileAdmin(admin.ModelAdmin):
    list_display = ("shop_name", "phone", "currency", "language", "low_stock_alert_limit")
    search_fields = ("shop_name", "phone", "address")


@admin.register(SecuritySetting)
class SecuritySettingAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    search_fields = ("user__username",)


@admin.register(ExportLog)
class ExportLogAdmin(admin.ModelAdmin):
    list_display = ("module", "file_type", "generated_by", "created_at")
    list_filter = ("module", "file_type", "created_at")

# Register your models here.
