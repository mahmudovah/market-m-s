from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.utils import timezone

from .models import Debt, DebtPayment, Debtor


def qarzdor_dashboard(request):
    today = timezone.localdate()
    totals = Debt.objects.aggregate(
        jami_qarz=Coalesce(Sum("remaining_amount"), Value(0)),
    )
    totals["jami_qarzdor"] = Debtor.objects.count()
    totals["muddati_otgan"] = Debt.objects.filter(
        due_date__lt=today, remaining_amount__gt=0
    ).count()
    totals["bugungi_qaytimlar"] = (
        DebtPayment.objects.filter(paid_at__date=today).aggregate(v=Coalesce(Sum("amount"), Value(0)))["v"]
    )
    return JsonResponse(totals)


def debt_list(request):
    debts = Debt.objects.select_related("debtor", "product").values(
        "id",
        "debtor__full_name",
        "debtor__phone",
        "product__name",
        "amount",
        "remaining_amount",
        "issued_at",
        "due_date",
        "status",
    )[:200]
    return JsonResponse({"results": list(debts)})


def reminders(request):
    today = timezone.localdate()
    overdue = Debt.objects.filter(due_date__lt=today, remaining_amount__gt=0).values(
        "id",
        "debtor__full_name",
        "debtor__phone",
        "remaining_amount",
        "due_date",
    )
    return JsonResponse({"results": list(overdue)})

# Create your views here.
