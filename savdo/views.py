from decimal import Decimal

from django.contrib import messages
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ombor.models import StockMovement
from core.pdf_utils import build_simple_pdf
from profil.models import ExportLog
from toifa.models import Product

from .forms import POSSaleForm
from .models import Sale, SaleItem, latest_product_cost


def _current_stock_for_product(product: Product) -> Decimal:
    qty_field = DecimalField(max_digits=14, decimal_places=3)
    qty_zero = Value(0, output_field=qty_field)
    agg = StockMovement.objects.filter(product=product).aggregate(
        kirim=Coalesce(
            Sum("quantity", filter=Q(movement_type=StockMovement.TYPE_IN), output_field=qty_field),
            qty_zero,
            output_field=qty_field,
        ),
        chiqim=Coalesce(
            Sum("quantity", filter=Q(movement_type=StockMovement.TYPE_OUT), output_field=qty_field),
            qty_zero,
            output_field=qty_field,
        ),
    )
    return agg["kirim"] - agg["chiqim"]


def pos_page(request):
    if request.method == "POST":
        form = POSSaleForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data["product"]
            quantity = form.cleaned_data["quantity"]
            available = _current_stock_for_product(product)
            if quantity > available:
                form.add_error("quantity", f"Yetarli zaxira yo'q. Mavjud: {available}")
            else:
                sale = Sale.objects.create(
                    customer_name=form.cleaned_data["customer_name"],
                    note=form.cleaned_data["note"],
                    sold_at=timezone.now(),
                    operator=request.user if request.user.is_authenticated else None,
                    cash_account=form.cleaned_data["cash_account"],
                )
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=form.cleaned_data["unit_price"],
                    purchase_price_at_sale=latest_product_cost(product),
                )
                sale.finalize()
                messages.success(request, f"Sotuv yaratildi. Chek raqami: {sale.pk}")
                return redirect("sale-receipt", sale_id=sale.pk)
    else:
        form = POSSaleForm()
        form.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("name")
        form.fields["cash_account"].queryset = form.fields["cash_account"].queryset.order_by("name")
        default_product = form.fields["product"].queryset.first()
        if default_product:
            form.fields["unit_price"].initial = default_product.sale_price

    recent_sales = Sale.objects.select_related("cash_account").prefetch_related("items__product").order_by("-sold_at")[:10]
    return render(request, "savdo_pos.html", {"form": form, "recent_sales": recent_sales})


def sale_receipt(request, sale_id: int):
    sale = get_object_or_404(Sale.objects.select_related("cash_account").prefetch_related("items__product"), pk=sale_id)
    return render(request, "receipt.html", {"sale": sale})


def profit_report(request):
    money_field = DecimalField(max_digits=14, decimal_places=2)
    money_zero = Value(0, output_field=money_field)
    totals = Sale.objects.filter(is_finalized=True).aggregate(
        revenue=Coalesce(Sum("total_amount", output_field=money_field), money_zero, output_field=money_field),
        cost=Coalesce(Sum("total_cost", output_field=money_field), money_zero, output_field=money_field),
        profit=Coalesce(Sum("profit_amount", output_field=money_field), money_zero, output_field=money_field),
    )
    by_month = (
        Sale.objects.filter(is_finalized=True)
        .annotate(month=TruncMonth("sold_at"))
        .values("month")
        .annotate(
            revenue=Coalesce(Sum("total_amount", output_field=money_field), money_zero, output_field=money_field),
            cost=Coalesce(Sum("total_cost", output_field=money_field), money_zero, output_field=money_field),
            profit=Coalesce(Sum("profit_amount", output_field=money_field), money_zero, output_field=money_field),
        )
        .order_by("-month")[:12]
    )
    recent_sales = Sale.objects.filter(is_finalized=True).order_by("-sold_at")[:20]
    return render(
        request,
        "profit_report.html",
        {"totals": totals, "by_month": by_month, "recent_sales": recent_sales},
    )


def export_sales_excel(request):
    try:
        from openpyxl import Workbook
    except Exception:
        return HttpResponse("openpyxl o'rnatilmagan", status=500)

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales"
    ws.append(["ID", "Sana", "Mijoz", "Tushum", "Tannarx", "Foyda"])
    for sale in Sale.objects.filter(is_finalized=True).order_by("-sold_at"):
        ws.append(
            [
                sale.id,
                sale.sold_at.strftime("%Y-%m-%d %H:%M"),
                sale.customer_name or "-",
                float(sale.total_amount),
                float(sale.total_cost),
                float(sale.profit_amount),
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="sales_report.xlsx"'
    wb.save(response)
    ExportLog.objects.create(module="Savdo", file_type=ExportLog.TYPE_EXCEL, generated_by=request.user if request.user.is_authenticated else None)
    return response


def export_sales_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="sales_report.pdf"'
    lines = []
    for sale in Sale.objects.filter(is_finalized=True).order_by("-sold_at")[:60]:
        lines.append(
            f"#{sale.id} | {sale.sold_at:%d.%m.%Y} | {sale.customer_name or '-'} | tushum={sale.total_amount} | tannarx={sale.total_cost} | foyda={sale.profit_amount}"
        )
    response.write(build_simple_pdf("Savdo hisoboti", lines))
    ExportLog.objects.create(module="Savdo", file_type=ExportLog.TYPE_PDF, generated_by=request.user if request.user.is_authenticated else None)
    return response

# Create your views here.
