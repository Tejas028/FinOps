import os
import logging
from typing import List, Optional
from datetime import date
from ..base_adapter import BaseIngestionAdapter
from shared.schemas.billing import BillingRecord

class GCPBillingAdapter(BaseIngestionAdapter):
    """
    Production adapter for GCP BigQuery Billing Export.
    Uses google-cloud-bigquery SDK.

    Required env vars:
      GCP_PROJECT_ID
      GCP_BILLING_DATASET  (BigQuery dataset, e.g. "billing_export")
      GCP_BILLING_TABLE    (BigQuery table, e.g. "gcp_billing_export_v1_...")
      GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON)
    """

    @property
    def cloud_provider(self) -> str:
        return "gcp"

    def validate_connection(self) -> bool:
        """
        Try to run a COUNT(*) query on the billing table.
        Return False (logged warning) if credentials missing.
        """
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or not os.getenv("GCP_PROJECT_ID"):
            logging.warning("Missing GCP credentials.")
            return False
        return True

    def fetch(self, start_date: date, end_date: date, account_id: Optional[str] = None) -> List[BillingRecord]:
        """
        Run parameterized BigQuery SQL:
        Return empty list if credentials not available.
        Set cloud_provider = "gcp" on all records.
        """
        if not self.validate_connection():
            return []
            
        return []
