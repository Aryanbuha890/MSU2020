from datetime import date
from decimal import Decimal

from django.conf import settings
from django.utils import timezone


import logging
import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

def usd_to_inr_rate() -> Decimal:
    """Fetch 1 USD to INR rate from API, cache for 12 hours. Fallback to settings or default."""
    cache_key = "usd_to_inr_realtime_rate"
    cached_rate = cache.get(cache_key)
    
    if cached_rate:
        return cached_rate
        
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        response.raise_for_status()
        data = response.json()
        inr_rate = Decimal(str(data["rates"]["INR"])).quantize(Decimal("0.01"))
        
        # Cache for 12 hours
        cache.set(cache_key, inr_rate, 60 * 60 * 12)
        return inr_rate
    except Exception as e:
        logger.error(f"Failed to fetch realtime exchange rate: {e}")
        # Fallback
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
