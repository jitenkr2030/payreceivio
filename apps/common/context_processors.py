"""Context processors available to all templates."""
from django.conf import settings


def global_settings(request):
    """Expose app-wide settings to templates."""
    return {
        "APP_NAME": settings.PAYRECEIVIO["COMPANY_NAME"],
        "APP_TAGLINE": settings.PAYRECEIVIO["TAGLINE"],
        "CURRENCY_SYMBOL": settings.PAYRECEIVIO["CURRENCY_SYMBOL"],
        "AGEING_BUCKETS": settings.PAYRECEIVIO["AGEING_BUCKETS"],
        "REMINDER_SCHEDULE": settings.PAYRECEIVIO["REMINDER_SCHEDULE"],
    }
