from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
import uuid

class NormalizedRecord(BaseModel):

    # ── Identity ──────────────────────────────────────────────
    record_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    # Deterministic fingerprint for deduplication.
    # SHA-256 of: cloud_provider + account_id + service_name_raw
    #             + usage_date.isoformat() + str(round(cost_usd, 6))
    fingerprint: str

    # ── Source (preserved from BillingRecord) ─────────────────
    cloud_provider: str           # "aws" | "azure" | "gcp"
    account_id: str
    service_name_raw: str         # original value, unchanged
    service_category: str         # normalized: see SERVICE MAP below
    region: str                   # normalized: see REGION MAP below
    resource_id: Optional[str]

    # ── Time ──────────────────────────────────────────────────
    usage_date: date
    ingested_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    # ── Cost ──────────────────────────────────────────────────
    cost_original: float          # raw cost in original currency
    currency_original: str        # e.g. "USD", "EUR", "INR"
    cost_usd: float               # normalized to USD
    usage_quantity: Optional[float]
    usage_unit: Optional[str]

    # ── Tags (parsed) ─────────────────────────────────────────
    tags_raw: str                 # original JSON string (from BillingRecord.tags)
    tags: Dict[str, Any]          # parsed dict (normalization layer parses it)

    # ── Enrichment ────────────────────────────────────────────
    environment: Optional[str]    # extracted from tags: "prod"|"staging"|"dev"|"unknown"
    team: Optional[str]           # extracted from tags: team/owner/squad key
    anomaly_flag: bool = False    # set by anomaly detection later; default False
    anomaly_severity: Optional[str] = None  # None until anomaly module runs

    class Config:
        json_encoders = {date: str, datetime: str}
