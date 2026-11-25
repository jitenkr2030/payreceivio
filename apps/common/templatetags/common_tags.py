"""Common template tags."""
from django import template

register = template.Library()


@register.filter
def lookup(d, key):
    """Lookup a key in a dict."""
    if d is None:
        return None
    if isinstance(d, dict):
        return d.get(key)
    return getattr(d, key, None)


@register.filter
def currency(value):
    """Format as Indian Rupees."""
    if value is None:
        return "₹0.00"
    try:
        from apps.common.utils import format_currency
        return format_currency(value)
    except Exception:
        return f"₹{value}"
