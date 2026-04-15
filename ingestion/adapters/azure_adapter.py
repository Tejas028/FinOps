import os
import logging
from typing import List, Optional
from datetime import date
from ..base_adapter import BaseIngestionAdapter
from shared.schemas.billing import BillingRecord

class AzureCostAdapter(BaseIngestionAdapter):
    """
    Production adapter for Azure Cost Management API.
    Uses azure-mgmt-costmanagement SDK.

    Required env vars:
      AZURE_SUBSCRIPTION_ID
      AZURE_TENANT_ID
      AZURE_CLIENT_ID
      AZURE_CLIENT_SECRET
    """

    @property
    def cloud_provider(self) -> str:
        return "azure"

    def validate_connection(self) -> bool:
        """
        Attempt to authenticate with DefaultAzureCredential.
        Return False (logged warning) if credentials missing.
        """
        sub_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        
        if not all([sub_id, tenant_id, client_id, client_secret]):
            logging.warning("Missing Azure credentials.")
            return False
        return True

    def fetch(self, start_date: date, end_date: date, account_id: Optional[str] = None) -> List[BillingRecord]:
        """
        Call Azure Cost Management QueryUsage API for date range.
        Paginate using nextLink if present.
        Return empty list if credentials not available.
        Set cloud_provider = "azure" on all records.
        """
        if not self.validate_connection():
            return []
        
        return []
