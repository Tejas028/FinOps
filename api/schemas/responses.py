from pydantic import BaseModel, Field
from typing import Generic, List, Optional, TypeVar, Dict
from datetime import datetime, date

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    data:        List[T]
    total:       int          # total matching rows (pre-pagination)
    page:        int
    page_size:   int
    has_next:    bool

class ErrorResponse(BaseModel):
    error:       str
    detail:      Optional[str] = None
    timestamp:   datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status:      str          # "ok" | "degraded" | "down"
    version:     str
    db_connected: bool
    uptime_seconds: float

# ─── Billing-specific responses ─────────────────────────────────

class BillingSummary(BaseModel):
    """Aggregated daily spend — NOT raw records (too large)"""
    usage_date:       date
    cloud_provider:   str
    service:          str
    region:           Optional[str]
    total_cost_usd:   float
    record_count:     int
    anomaly_count:    int

class SpendByDimension(BaseModel):
    """For /billing/by-cloud, /billing/by-service responses"""
    dimension:        str           # cloud name, service name, etc.
    total_cost_usd:   float
    pct_of_total:     float
    record_count:     int

# ─── Anomaly-specific responses ─────────────────────────────────

class AnomalyListItem(BaseModel):
    """Lightweight anomaly record for list views"""
    anomaly_id:       str
    record_id:        str
    detection_method: str
    severity:         str
    z_score:          Optional[float]
    expected_cost:    float
    actual_cost:      float
    deviation_pct:    float
    detected_at:      datetime
    # Denormalized from billing join:
    cloud_provider:   str
    service:          str
    region:           Optional[str]
    usage_date:       date

class AnomalySummary(BaseModel):
    """For /anomalies/summary endpoint"""
    total_anomalies:  int
    by_severity:      Dict[str, int]
    by_cloud:         Dict[str, int]
    by_type:          Dict[str, int]
    date_range:       Dict[str, str]  # {"start": "...", "end": "..."}

# ─── Forecast-specific responses ────────────────────────────────

class ForecastListItem(BaseModel):
    forecast_id:      str
    cloud_provider:   str
    service:          str
    region:           Optional[str]
    horizon_days: int
    forecast_date:    date
    predicted_cost:   float
    lower_bound:      float
    upper_bound: float
    model_used:       str
    generated_at:     datetime

class BudgetRiskResponse(BaseModel):
    breach_risk:      str  # "none" | "possible" | "likely" | "certain"
    breach_date:      Optional[str]
    projected_monthly_cost: float
    monthly_budget_usd:    float
    confidence_pct:   float = 95.0
    days_to_breach:   Optional[int] = None
    cloud_provider:   Optional[str] = None


# ─── Attribution-specific responses ─────────────────────────────

class AttributionListItem(BaseModel):
    attribution_date: date
    cloud_provider:   str
    service_category: str
    account_id:       str
    environment:      str
    team:             str
    total_cost_usd:   float
    top_driver_1:     Optional[str]
    top_driver_1_value: Optional[float]
    top_driver_2:     Optional[str]
    top_driver_2_value: Optional[float]
    top_driver_3:     Optional[str]
    top_driver_3_value: Optional[float]
    model_r2_score:   Optional[float]
    shap_values:      Dict[str, float]

# ─── Alert-specific responses ─────────────────────────────

class AlertListItem(BaseModel):
    alert_id:        str
    alert_type:      str
    severity:        str
    cloud_provider:  str
    service_category: Optional[str]
    alert_date:      str
    title:           str
    message:         str
    is_resolved:     bool
    created_at:      str
