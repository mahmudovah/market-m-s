from django.contrib import admin

from .models import Debt, DebtPayment, Debtor


class DebtPaymentInline(admin.TabularInline):
    model = DebtPayment
    extra = 0


@admin.register(Debtor)
class DebtorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "created_at")
    search_fields = ("full_name", "phone")


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ("debtor", "amount", "remaining_amount", "issued_at", "due_date", "status")
    list_filter = ("status", "due_date")
    search_fields = ("debtor__full_name", "note")
    inlines = (DebtPaymentInline,)

# Register your models here.
