from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from core.pdf_utils import build_simple_pdf
from profil.models import ExportLog
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


def export_debt_excel(request):
    try:
        from openpyxl import Workbook
    except Exception:
        return HttpResponse("openpyxl o'rnatilmagan", status=500)

    wb = Workbook()
    ws = wb.active
    ws.title = "Debts"
    ws.append(["ID", "Qarzdor", "Telefon", "Jami", "Qoldiq", "Muddat", "Status"])
    for d in Debt.objects.select_related("debtor").order_by("-issued_at")[:1000]:
        ws.append(
            [
                d.id,
                d.debtor.full_name,
                d.debtor.phone,
                float(d.amount),
                float(d.remaining_amount),
                d.due_date.strftime("%Y-%m-%d"),
                d.status,
            ]
        )
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="qarzdor_report.xlsx"'
    wb.save(response)
    ExportLog.objects.create(module="Qarzdor", file_type=ExportLog.TYPE_EXCEL, generated_by=request.user if request.user.is_authenticated else None)
    return response


def export_debt_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="qarzdor_report.pdf"'
    lines = []
    for d in Debt.objects.select_related("debtor").order_by("-issued_at")[:120]:
        lines.append(
            f"#{d.id} | {d.debtor.full_name} | qoldiq={d.remaining_amount} | muddat={d.due_date:%d.%m.%Y} | {d.status}"
        )
    response.write(build_simple_pdf("Qarzdor hisoboti", lines))
    ExportLog.objects.create(module="Qarzdor", file_type=ExportLog.TYPE_PDF, generated_by=request.user if request.user.is_authenticated else None)
    return response

# Create your views here.
