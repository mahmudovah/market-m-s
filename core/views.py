from datetime import timedelta
from urllib.parse import quote

from django.db.models import BooleanField, Case, Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce, TruncMonth
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone

from kassa.models import CashTransaction, CashTransfer
from ombor.models import StockMovement, WarehouseReceipt
from profil.models import ExportLog, ShopProfile
from qarzdor.models import Debt, DebtPayment
from savdo.models import Sale, SaleItem
from toifa.models import Category, Product


def _is_admin_like(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def _stock_with_low_flags():
    qty_field = DecimalField(max_digits=14, decimal_places=3)
    qty_zero = Value(0, output_field=qty_field)
    current_stock = (
        Product.objects.annotate(
            kirim=Coalesce(
                Sum(
                    "stock_movements__quantity",
                    filter=Q(stock_movements__movement_type=StockMovement.TYPE_IN),
                    output_field=qty_field,
                ),
                qty_zero,
                output_field=qty_field,
            ),
            chiqim=Coalesce(
                Sum(
                    "stock_movements__quantity",
                    filter=Q(stock_movements__movement_type=StockMovement.TYPE_OUT),
                    output_field=qty_field,
                ),
                qty_zero,
                output_field=qty_field,
            ),
        )
        .annotate(current_qty=ExpressionWrapper(F("kirim") - F("chiqim"), output_field=qty_field))
        .annotate(
            is_low=Case(
                When(current_qty__lte=F("min_stock_limit"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .order_by("name")
    )
    return current_stock


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


@login_required
@user_passes_test(_is_admin_like, login_url="/operator/")
def dashboard(request):
    period = request.GET.get("period", "30")
    period_days = 30
    if period in {"7", "30", "90"}:
        period_days = int(period)
    period_start = timezone.now() - timedelta(days=period_days)

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
    sales_profit = Sale.objects.filter(is_finalized=True).aggregate(
        total=Coalesce(Sum("profit_amount", output_field=money_field), money_zero, output_field=money_field)
    )["total"]

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
            "jami_foyda": sales_profit,
            "otkazmalar": CashTransfer.objects.count(),
        },
        "low_stock_items": low_stock,
        "recent_exports": ExportLog.objects.select_related("generated_by").order_by("-created_at")[:8],
        "modules": [
            {"name": "Toifa", "desc": "Toifalar, mahsulotlar, narxlar", "url_name": "web-toifa"},
            {"name": "Ombor", "desc": "Kirim, chiqim, zaxira nazorati", "url_name": "web-ombor"},
            {"name": "Savdo", "desc": "POS, chek, foyda-zarar", "url_name": "web-pos"},
            {"name": "Kassa", "desc": "Pul oqimi va oyma-oy taqqoslash", "url_name": "web-kassa"},
            {"name": "Qarzdor", "desc": "Qarzlar va qaytimlar", "url_name": "web-qarzdor"},
            {"name": "Profil", "desc": "Do'kon ma'lumotlari va sozlamalar", "url_name": "web-profil"},
        ],
        "top_products": (
            SaleItem.objects.filter(sale__is_finalized=True, sale__sold_at__gte=period_start)
            .values("product__name")
            .annotate(
                total_qty=Coalesce(Sum("quantity", output_field=qty_field), qty_zero, output_field=qty_field),
                total_revenue=Coalesce(
                    Sum(F("quantity") * F("unit_price"), output_field=money_field),
                    money_zero,
                    output_field=money_field,
                ),
            )
            .order_by("-total_qty")[:10]
        ),
        "period_days": period_days,
    }
    return render(request, "dashboard.html", context)


@login_required
@user_passes_test(_is_admin_like, login_url="/operator/")
def web_ombor(request):
    current_stock = _stock_with_low_flags()
    receipts = list(WarehouseReceipt.objects.select_related("operator").order_by("-received_at")[:20])
    for receipt in receipts:
        receipt.qr_image_url = f"https://quickchart.io/qr?size=140&text={quote(receipt.qr_payload)}"
    movements = StockMovement.objects.select_related("product", "operator").order_by("-moved_at")[:20]
    context = {"current_stock": current_stock, "receipts": receipts, "movements": movements}
    return render(request, "ombor.html", context)


@login_required
def web_kassa(request):
    if not _is_admin_like(request.user):
        return redirect("operator-dashboard")

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


@login_required
def web_qarzdor(request):
    if not _is_admin_like(request.user):
        return redirect("operator-dashboard")

    today = timezone.localdate()
    active_debts = Debt.objects.filter(due_date__gte=today, remaining_amount__gt=0).select_related("debtor", "product").order_by("-issued_at")[:20]
    overdue = Debt.objects.filter(due_date__lt=today, remaining_amount__gt=0).select_related("debtor", "product")[:20]
    closed = Debt.objects.filter(remaining_amount__lte=0).select_related("debtor", "product").order_by("-issued_at")[:20]
    today_payments = DebtPayment.objects.filter(paid_at__date=today).select_related("debt__debtor")[:10]
    context = {
        "active_debts": active_debts,
        "overdue": overdue,
        "closed": closed,
        "today_payments": today_payments,
    }
    return render(request, "qarzdor.html", context)


@login_required
def web_toifa(request):
    categories = Category.objects.annotate(product_count=Count("products"))
    selected_category = request.GET.get("category")
    products = []
    selected_category_obj = None
    if selected_category:
        selected_category_obj = categories.filter(pk=selected_category).first()
        if selected_category_obj:
            products = Product.objects.select_related("category").filter(category=selected_category_obj).order_by("name")
    return render(
        request,
        "toifa.html",
        {"categories": categories, "products": products, "selected_category": selected_category_obj},
    )


@login_required
def web_profil(request):
    profile = ShopProfile.objects.order_by("-id").first()
    exports = ExportLog.objects.select_related("generated_by").order_by("-created_at")[:20]
    return render(request, "profil.html", {"profile": profile, "exports": exports})


@login_required
def operator_dashboard(request):
    current_stock = _stock_with_low_flags()
    low_items = [row for row in current_stock if row.is_low][:20]
    context = {
        "cards": {
            "toifalar": Category.objects.count(),
            "mahsulotlar": Product.objects.count(),
            "kam_qolganlar": len(low_items),
            "bugungi_sotuvlar": Sale.objects.filter(sold_at__date=timezone.localdate()).count(),
        },
        "low_stock_items": low_items,
        "modules": [
            {"name": "Toifa va Mahsulot", "url_name": "web-toifa"},
            {"name": "Ombor (qoldiq)", "url_name": "operator-ombor"},
            {"name": "POS / Chek", "url_name": "web-pos"},
            {"name": "Profil", "url_name": "web-profil"},
        ],
    }
    return render(request, "operator_dashboard.html", context)


@login_required
def operator_ombor(request):
    stock_rows = _stock_with_low_flags()
    return render(request, "operator_ombor.html", {"stock_rows": stock_rows})
