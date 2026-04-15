import os
import glob
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import date
from ..base_adapter import BaseIngestionAdapter
from shared.schemas.billing import BillingRecord
from shared.utils.parquet_utils import read_parquet_records
import pandas as pd

class SyntheticAdapter(BaseIngestionAdapter):
    def __init__(self, data_root: str = "synthetic_data/output"):
        self.data_root = Path(data_root)

    @property
    def cloud_provider(self) -> str:
        return "all"   # special value for the synthetic adapter

    def validate_connection(self) -> bool:
        """Return True if synthetic_data/output/ exists and has parquet files."""
        if not self.data_root.exists() or not self.data_root.is_dir():
            return False
        # Check combined or specific
        combined_path = self.data_root / "combined" / "all_clouds_billing.parquet"
        if combined_path.exists():
            return True
        for cp in ['aws', 'azure', 'gcp']:
            if list((self.data_root / cp).glob("*.parquet")):
                return True
        return False

    def fetch(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None,   # "aws" | "azure" | "gcp" | None (all)
        account_id: Optional[str] = None
    ) -> List[BillingRecord]:
        """
        Read parquet files from synthetic_data/output/{cloud_provider}/*.parquet
        Filter by usage_date >= start_date and usage_date <= end_date.
        If cloud_provider is None, read all three clouds.
        If account_id is specified, filter by that account.
        """
        records = read_parquet_records(
            path=str(self.data_root),
            cloud_provider=cloud_provider,
            start_date=start_date,
            end_date=end_date
        )
        
        if account_id:
            records = [r for r in records if r.account_id == account_id]
            
        records.sort(key=lambda r: r.usage_date)
        return records

    def fetch_by_cloud(self, cloud_provider: str, start_date: date, end_date: date) -> List[BillingRecord]:
        """Convenience method — fetches single cloud only."""
        return self.fetch(start_date=start_date, end_date=end_date, cloud_provider=cloud_provider)

    def get_available_date_range(self, cloud_provider: Optional[str] = None) -> Tuple[date, date]:
        """Return (min_usage_date, max_usage_date) across all parquet files."""
        # We only need to check the combined dataframe or min/max overall without loading all into memory
        # For simplicity in synthetic adapter, load one specific or combined
        try:
            records = read_parquet_records(
                path=str(self.data_root),
                cloud_provider=cloud_provider
            )
            if not records:
                return date.today(), date.today()
            min_d = min(r.usage_date for r in records)
            max_d = max(r.usage_date for r in records)
            return min_d, max_d
        except Exception:
            return date.today(), date.today()
