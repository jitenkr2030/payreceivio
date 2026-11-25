"""Shared utilities for the PayReceivio platform."""
from __future__ import annotations

import decimal
from datetime import date, datetime, timedelta
from typing import Iterable, Tuple


def format_currency(amount: decimal.Decimal | float | int | None, symbol: str = "₹") -> str:
    """Format an amount in Indian numbering system (lakh/crore)."""
    if amount is None:
        amount = 0
    if isinstance(amount, (float, int)):
        amount = decimal.Decimal(str(amount))
    amount = amount.quantize(decimal.Decimal("0.01"))
    integer_part = int(amount)
    decimal_part = str(amount).split(".")[1] if "." in str(amount) else "00"
    s = str(abs(integer_part))
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        # Group first 2, then groups of 2
        groups = [rest[-2:]] if len(rest) >= 2 else [rest]
        rest = rest[:-2] if len(rest) >= 2 else ""
        while rest:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        formatted = ",".join(groups) + "," + last3
    else:
        formatted = s
    sign = "-" if integer_part < 0 else ""
    return f"{symbol}{sign}{formatted}.{decimal_part}"


def ageing_bucket(days_overdue: int) -> str:
    """Return the ageing bucket key for a given number of days overdue."""
    if days_overdue <= 0:
        return "current"
    elif days_overdue <= 30:
        return "1-30"
    elif days_overdue <= 60:
        return "31-60"
    elif days_overdue <= 90:
        return "61-90"
    elif days_overdue <= 180:
        return "91-180"
    return "180+"


def ageing_bucket_label(bucket: str) -> str:
    return {
        "current": "Current",
        "1-30": "1-30 days",
        "31-60": "31-60 days",
        "61-90": "61-90 days",
        "91-180": "91-180 days",
        "180+": "Above 180 days",
    }.get(bucket, bucket)


def days_between(d1: date, d2: date) -> int:
    return (d1 - d2).days


def generate_invoice_number(prefix: str = "INV", sequence: int = 1, year: int | None = None) -> str:
    """Generate a zero-padded invoice number."""
    if year is None:
        year = date.today().year
    return f"{prefix}/{year}/{sequence:06d}"


def parse_amount(value) -> decimal.Decimal:
    """Parse a string/float into a Decimal safely."""
    if value is None or value == "":
        return decimal.Decimal("0")
    if isinstance(value, decimal.Decimal):
        return value
    if isinstance(value, (int, float)):
        return decimal.Decimal(str(value))
    return decimal.Decimal(str(value).replace(",", "").strip())


def chunk(iterable: Iterable, size: int):
    """Yield successive chunks from an iterable."""
    chunk_list = []
    for item in iterable:
        chunk_list.append(item)
        if len(chunk_list) == size:
            yield chunk_list
            chunk_list = []
    if chunk_list:
        yield chunk_list
