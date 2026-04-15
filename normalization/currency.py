import logging
from typing import Dict

class CurrencyNormalizer:
    # Static fallback rates (relative to USD)
    STATIC_RATES: Dict[str, float] = {
        "USD": 1.0,
        "EUR": 1.08,
        "GBP": 1.27,
        "INR": 0.012,
        "AUD": 0.65,
        "CAD": 0.74,
        "JPY": 0.0067,
        "SGD": 0.74,
    }

    def to_usd(self, amount: float, currency: str) -> float:
        """
        Convert amount in `currency` to USD using static rates.
        If currency not in table, log a warning and return amount as-is.
        """
        rate = self.get_rate(currency)
        if rate == 1.0 and currency.upper() != "USD":
            logging.warning(f"Currency {currency} not found in static rates. Assuming 1:1 to USD.")
        return amount * rate

    def get_rate(self, currency: str) -> float:
        """Return the USD conversion rate for `currency`."""
        if not currency:
            return 1.0
        return self.STATIC_RATES.get(currency.upper(), 1.0)
