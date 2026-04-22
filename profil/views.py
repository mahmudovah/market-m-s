from django.http import JsonResponse

from .models import ExportLog, ShopProfile


def profile_settings(request):
    profile = ShopProfile.objects.order_by("-id").first()
    export_count = ExportLog.objects.count()
    if profile is None:
        return JsonResponse(
            {
                "profile": None,
                "message": "ShopProfile hali yaratilmagan. Admin paneldan qo'shing.",
                "export_log_count": export_count,
            }
        )
    return JsonResponse(
        {
            "profile": {
                "shop_name": profile.shop_name,
                "phone": profile.phone,
                "address": profile.address,
                "currency": profile.currency,
                "language": profile.language,
                "notification_phone": profile.notification_phone,
                "low_stock_alert_limit": profile.low_stock_alert_limit,
            },
            "export_log_count": export_count,
        }
    )

# Create your views here.
