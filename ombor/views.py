from django.db.models import Case, DecimalField, ExpressionWrapper, F, Sum, Value, When
from django.db.models.functions import Coalesce
from django.http import JsonResponse

from .models import StockMovement, WarehouseReceipt, WarehouseReceiptItem


def ombor_dashboard(request):
    totals = StockMovement.objects.aggregate(
        jami_kirim=Coalesce(
            Sum(
                Case(
                    When(movement_type=StockMovement.TYPE_IN, then=F("quantity")),
                    default=Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=3),
                )
            ),
            Value(0),
        ),
        jami_chiqim=Coalesce(
            Sum(
                Case(
                    When(movement_type=StockMovement.TYPE_OUT, then=F("quantity")),
                    default=Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=3),
                )
            ),
            Value(0),
        ),
    )
    totals["hozirgi_zaxira"] = totals["jami_kirim"] - totals["jami_chiqim"]
    return JsonResponse(totals)


def stock_summary(request):
    rows = (
        StockMovement.objects.values("product__id", "product__name", "product__min_stock_limit")
        .annotate(
            kirim=Coalesce(
                Sum(
                    Case(
                        When(movement_type=StockMovement.TYPE_IN, then=F("quantity")),
                        default=Value(0),
                        output_field=DecimalField(max_digits=14, decimal_places=3),
                    )
                ),
                Value(0),
            ),
            chiqim=Coalesce(
                Sum(
                    Case(
                        When(movement_type=StockMovement.TYPE_OUT, then=F("quantity")),
                        default=Value(0),
                        output_field=DecimalField(max_digits=14, decimal_places=3),
                    )
                ),
                Value(0),
            ),
        )
        .order_by("product__name")
    )
    results = []
    for row in rows:
        current_stock = row["kirim"] - row["chiqim"]
        row["joriy_qoldiq"] = current_stock
        row["kam_qolgan"] = current_stock <= row["product__min_stock_limit"]
        results.append(row)
    return JsonResponse({"results": results})


def movement_history(request):
    movements = StockMovement.objects.select_related("product").values(
        "id",
        "product__name",
        "movement_type",
        "quantity",
        "unit_price",
        "moved_at",
        "source",
        "note",
    )[:200]
    return JsonResponse({"results": list(movements)})


def receipt_cost_report(request):
    total_cost_expr = ExpressionWrapper(F("quantity") * F("unit_cost"), output_field=DecimalField())
    report = (
        WarehouseReceiptItem.objects.values("product__name")
        .annotate(jami_miqdor=Sum("quantity"), jami_tannarx=Sum(total_cost_expr))
        .order_by("product__name")
    )
    recent_receipts = WarehouseReceipt.objects.values("id", "supplier_name", "received_at")[:20]
    return JsonResponse({"cost_report": list(report), "recent_receipts": list(recent_receipts)})

# Create your views here.
