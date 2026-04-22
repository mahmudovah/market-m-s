from django.db.models import Case, Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce, TruncMonth
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from kassa.models import CashTransaction, CashTransfer
from ombor.models import StockMovement
from profil.models import ExportLog, ShopProfile
from qarzdor.models import Debt, DebtPayment
from toifa.models import Category, Product


def api_root(request):
    return JsonResponse(
        {
            "project": "Bozor boshqaruv tizimi",
            "modules": {
                "toifa": "/api/toifa/",
                "ombor": "/api/ombor/",
                "kassa": "/api/kassa/",
                "qarzdor": "/api/qarzdor/",
                "profil": "/api/profil/",
            },
        }
    )


def dashboard(request):
    qty_field = DecimalField(max_digits=14, decimal_places=3)
    money_field = DecimalField(max_digits=14, decimal_places=2)
    qty_zero = Value(0, output_field=qty_field)
    money_zero = Value(0, output_field=money_field)

    stock = StockMovement.objects.aggregate(
        jami_kirim=Coalesce(
            Sum(
                Case(
                    When(movement_type=StockMovement.TYPE_IN, then=F("quantity")),
                    default=qty_zero,
                    output_field=qty_field,
                )
            ),
            qty_zero,
        ),
        jami_chiqim=Coalesce(
            Sum(
                Case(
                    When(movement_type=StockMovement.TYPE_OUT, then=F("quantity")),
                    default=qty_zero,
                    output_field=qty_field,
                )
            ),
            qty_zero,
        ),
    )
    cash = CashTransaction.objects.aggregate(
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
    debt_total = Debt.objects.aggregate(total=Coalesce(Sum("remaining_amount"), money_zero))["total"]

    low_stock = (
        Product.objects.annotate(
            kirim=Coalesce(
                Sum("stock_movements__quantity", filter=Q(stock_movements__movement_type=StockMovement.TYPE_IN)),
                qty_zero,
            ),
            chiqim=Coalesce(
                Sum("stock_movements__quantity", filter=Q(stock_movements__movement_type=StockMovement.TYPE_OUT)),
                qty_zero,
            ),
        )
        .annotate(current_stock=ExpressionWrapper(F("kirim") - F("chiqim"), output_field=qty_field))
        .filter(current_stock__lte=F("min_stock_limit"))
        .select_related("category")
        .order_by("current_stock")[:7]
    )

    context = {
        "cards": {
            "toifalar": Category.objects.count(),
            "mahsulotlar": Product.objects.count(),
            "hozirgi_zaxira": stock["jami_kirim"] - stock["jami_chiqim"],
            "kassa_qoldiq": cash["jami_kirim"] - cash["jami_chiqim"],
            "jami_qarz": debt_total,
            "otkazmalar": CashTransfer.objects.count(),
        },
        "low_stock_items": low_stock,
        "recent_exports": ExportLog.objects.select_related("generated_by").order_by("-created_at")[:8],
        "modules": [
            {"name": "Toifa", "desc": "Toifalar, mahsulotlar, narxlar", "url_name": "web-toifa"},
            {"name": "Ombor", "desc": "Kirim, chiqim, zaxira nazorati", "url_name": "web-ombor"},
            {"name": "Kassa", "desc": "Pul oqimi va oyma-oy taqqoslash", "url_name": "web-kassa"},
            {"name": "Qarzdor", "desc": "Qarzlar va qaytimlar", "url_name": "web-qarzdor"},
            {"name": "Profil", "desc": "Do'kon ma'lumotlari va sozlamalar", "url_name": "web-profil"},
        ],
    }
    return render(request, "dashboard.html", context)


def web_ombor(request):
    movements = StockMovement.objects.select_related("product").order_by("-moved_at")[:20]
    context = {"movements": movements}
    return render(request, "ombor.html", context)


def web_kassa(request):
    money_field = DecimalField(max_digits=14, decimal_places=2)
    money_zero = Value(0, output_field=money_field)

    rows = (
        CashTransaction.objects.values("account__name", "account__account_type")
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
    accounts = []
    for row in rows:
        row["balance"] = row["kirim"] - row["chiqim"]
        accounts.append(row)

    monthly = (
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
        .order_by("-month")[:6]
    )
    monthly_rows = []
    for row in monthly:
        row["qoldiq"] = row["kirim"] - row["chiqim"]
        monthly_rows.append(row)

    return render(request, "kassa.html", {"accounts": accounts, "monthly_rows": monthly_rows})


def web_qarzdor(request):
    today = timezone.localdate()
    debts = Debt.objects.select_related("debtor", "product").order_by("-issued_at")[:20]
    overdue = Debt.objects.filter(due_date__lt=today, remaining_amount__gt=0).select_related("debtor")[:10]
    today_payments = DebtPayment.objects.filter(paid_at__date=today).select_related("debt__debtor")[:10]
    context = {
        "debts": debts,
        "overdue": overdue,
        "today_payments": today_payments,
    }
    return render(request, "qarzdor.html", context)


def web_toifa(request):
    categories = Category.objects.annotate(product_count=Count("products"))
    products = Product.objects.select_related("category").order_by("category__name", "name")[:30]
    return render(request, "toifa.html", {"categories": categories, "products": products})


def web_profil(request):
    profile = ShopProfile.objects.order_by("-id").first()
    exports = ExportLog.objects.select_related("generated_by").order_by("-created_at")[:20]
    return render(request, "profil.html", {"profile": profile, "exports": exports})
