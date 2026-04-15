from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from enum import Enum

class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"

class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BillingRecord(BaseModel):
    record_id: str
    cloud_provider: CloudProvider
    account_id: str
    service: str
    region: Optional[str] = None
    resource_id: Optional[str] = None
    usage_date: date                          # UTC date
    cost_usd: float
    original_cost: float
    original_currency: str
    exchange_rate: float
    tags: str                                  # JSON string — use json.loads() to read
    ingested_at: datetime
    is_anomaly: bool = False
    anomaly_type: Optional[str] = None
    anomaly_severity: Optional[AnomalySeverity] = None
    is_duplicate: bool = False
    is_backdated: bool = False
    notes: Optional[str] = None
