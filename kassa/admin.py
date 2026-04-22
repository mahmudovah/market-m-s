from django.contrib import admin

from .models import CashAccount, CashTransaction, CashTransfer


@admin.register(CashAccount)
class CashAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "account_type", "created_at")
    list_filter = ("account_type",)
    search_fields = ("name",)


@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ("account", "direction", "amount", "category", "occurred_at")
    list_filter = ("direction", "account", "occurred_at")
    search_fields = ("category", "source", "note")


@admin.register(CashTransfer)
class CashTransferAdmin(admin.ModelAdmin):
    list_display = ("from_account", "to_account", "amount", "occurred_at")
    list_filter = ("occurred_at",)

# Register your models here.
