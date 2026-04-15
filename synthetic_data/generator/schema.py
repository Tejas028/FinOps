from typing import Optional, Dict
from pydantic import BaseModel

class BillingRecord(BaseModel):
    record_id: str
    cloud_provider: str
    account_id: str
    service: str
    region: Optional[str]
    resource_id: Optional[str]
    usage_date: str
    cost_usd: float
    original_cost: float
    original_currency: str
    exchange_rate: float
    tags: Dict[str, str]
    ingested_at: str
    is_anomaly: bool
    anomaly_type: Optional[str] = None
    anomaly_severity: Optional[str] = None
    is_duplicate: bool
    is_backdated: bool
    notes: Optional[str] = None
