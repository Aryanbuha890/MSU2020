from datetime import date
from decimal import Decimal

from django.conf import settings
from django.utils import timezone


def usd_to_inr_rate() -> Decimal:
    """1 USD = X INR from MVP_EXCHANGE_RATES_TO_USD (INR per USD)."""
    rates = getattr(settings, "MVP_EXCHANGE_RATES_TO_USD", {"USD": "1", "INR": "0.012"})
    inr_per_usd = Decimal(str(rates.get("INR", "0.012")))
    if inr_per_usd <= 0:
        return Decimal("83.33")
    return (Decimal("1") / inr_per_usd).quantize(Decimal("0.01"))


def exchange_rate_context() -> dict:
    rate = usd_to_inr_rate()
    return {
        "usd_inr_rate": rate,
        "exchange_rate_label": f"1 USD = {rate} INR",
        "exchange_rate_date": timezone.localdate(),
    }


def convert_usd_amount(amount_usd: Decimal, display_currency: str) -> Decimal:
    if display_currency == "INR":
        return (amount_usd * usd_to_inr_rate()).quantize(Decimal("0.01"))
    return amount_usd.quantize(Decimal("0.01"))
