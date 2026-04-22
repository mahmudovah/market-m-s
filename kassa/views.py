from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce, TruncMonth
from django.http import JsonResponse

from .models import CashAccount, CashTransaction, CashTransfer


def kassa_dashboard(request):
    money_field = DecimalField(max_digits=14, decimal_places=2)
    money_zero = Value(0, output_field=money_field)

    totals = CashTransaction.objects.aggregate(
        jami_kirim=Coalesce(
            Sum(
                Case(
                    When(direction=CashTransaction.DIR_IN, then=F("amount")),
                    default=money_zero,
                    output_field=money_field,
                )
            ),
            money_zero,
        ),
        jami_chiqim=Coalesce(
            Sum(
                Case(
                    When(direction=CashTransaction.DIR_OUT, then=F("amount")),
                    default=money_zero,
                    output_field=money_field,
                )
            ),
            money_zero,
        ),
    )
    totals["sox_foyda"] = totals["jami_kirim"] - totals["jami_chiqim"]
    totals["otkazma_soni"] = CashTransfer.objects.count()
    return JsonResponse(totals)


def account_balances(request):
    money_field = DecimalField(max_digits=14, decimal_places=2)
    money_zero = Value(0, output_field=money_field)

    rows = (
        CashTransaction.objects.values("account__id", "account__name", "account__account_type")
        .annotate(
            kirim=Coalesce(
                Sum(
                    Case(
                        When(direction=CashTransaction.DIR_IN, then=F("amount")),
                        default=money_zero,
                        output_field=money_field,
                    )
                ),
                money_zero,
            ),
            chiqim=Coalesce(
                Sum(
                    Case(
                        When(direction=CashTransaction.DIR_OUT, then=F("amount")),
                        default=money_zero,
                        output_field=money_field,
                    )
                ),
                money_zero,
            ),
        )
        .order_by("account__account_type", "account__name")
    )
    results = []
    for row in rows:
        row["balance"] = row["kirim"] - row["chiqim"]
        results.append(row)
    return JsonResponse({"results": results, "accounts_count": CashAccount.objects.count()})


def monthly_compare(request):
    money_field = DecimalField(max_digits=14, decimal_places=2)
    money_zero = Value(0, output_field=money_field)

    rows = (
        CashTransaction.objects.annotate(month=TruncMonth("occurred_at"))
        .values("month")
        .annotate(
            kirim=Coalesce(
                Sum(
                    Case(
                        When(direction=CashTransaction.DIR_IN, then=F("amount")),
                        default=money_zero,
                        output_field=money_field,
                    )
                ),
                money_zero,
            ),
            chiqim=Coalesce(
                Sum(
                    Case(
                        When(direction=CashTransaction.DIR_OUT, then=F("amount")),
                        default=money_zero,
                        output_field=money_field,
                    )
                ),
                money_zero,
            ),
        )
        .order_by("-month")[:12]
    )
    results = []
    for row in rows:
        row["qoldiq"] = row["kirim"] - row["chiqim"]
        results.append(row)
    return JsonResponse({"results": results})

# Create your views here.
