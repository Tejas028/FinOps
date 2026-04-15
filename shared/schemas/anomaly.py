from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .billing import AnomalySeverity

class AnomalyResult(BaseModel):
    anomaly_id: str
    record_id: str
    detection_method: str                     # "zscore" | "isolation_forest" | "lstm"
    severity: AnomalySeverity
    z_score: Optional[float] = None
    expected_cost: float
    actual_cost: float
    deviation_pct: float
    detected_at: datetime
    shap_attribution: Optional[dict] = None   # populated by Module 8
