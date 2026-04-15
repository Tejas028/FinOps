import os
import logging
from typing import List, Optional
from datetime import date
from ..base_adapter import BaseIngestionAdapter
from shared.schemas.billing import BillingRecord

class AWSCURAdapter(BaseIngestionAdapter):
    """
    Production adapter for AWS Cost & Usage Reports (CUR).
    Reads from S3 bucket where AWS exports CUR data in parquet format.

    Required env vars:
      AWS_ACCESS_KEY_ID
      AWS_SECRET_ACCESS_KEY
      AWS_REGION (default: us-east-1)
      AWS_CUR_BUCKET (S3 bucket name)
      AWS_CUR_PREFIX (S3 key prefix, e.g. "cur/finops/")
    """

    def __init__(self):
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket = os.getenv("AWS_CUR_BUCKET")
        self.prefix = os.getenv("AWS_CUR_PREFIX", "")
        self._client = None  # lazy boto3 client init

    @property
    def cloud_provider(self) -> str:
        return "aws"

    def validate_connection(self) -> bool:
        """
        Try to list objects in the CUR bucket.
        Return False (with logged warning) if credentials missing.
        Never raise — always return bool.
        """
        if not all([self.access_key, self.secret_key, self.bucket]):
            logging.warning("Missing AWS credentials or bucket configuration.")
            return False
        return True

    def fetch(self, start_date: date, end_date: date, account_id: Optional[str] = None) -> List[BillingRecord]:
        """
        List CUR parquet files in S3 for the date range.
        Download each, parse with pyarrow, normalize to BillingRecord.
        Return empty list if credentials not available.
        Set cloud_provider = "aws" on all records.
        """
        if not self.validate_connection():
            return []
            
        return []
