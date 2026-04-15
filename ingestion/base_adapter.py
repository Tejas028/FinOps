from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date, timedelta
from shared.schemas.billing import BillingRecord

class BaseIngestionAdapter(ABC):

    @abstractmethod
    def fetch(
        self,
        start_date: date,
        end_date: date,
        account_id: Optional[str] = None
    ) -> List[BillingRecord]:
        """Fetch records for the given date range."""
        ...

    @abstractmethod
    def validate_connection(self) -> bool:
        """Check if the data source is reachable. Return False gracefully."""
        ...

    @property
    @abstractmethod
    def cloud_provider(self) -> str:
        """Return 'aws', 'azure', or 'gcp'."""
        ...

    def fetch_paginated(
        self,
        start_date: date,
        end_date: date,
        page_size: int = 10_000
    ) -> List[BillingRecord]:
        """
        Default chunked fetch implementation. Splits date range into
        30-day windows and calls self.fetch() per window. Subclasses
        may override for API-native pagination.
        """
        records = []
        current_start = start_date
        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=30), end_date)
            records.extend(self.fetch(current_start, current_end))
            current_start = current_end + timedelta(days=1)
        return records
