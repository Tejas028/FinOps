from pydantic import BaseModel
from typing import Dict, Optional
from datetime import date, datetime

class AttributionRecord(BaseModel):
    attribution_date:   date
    cloud_provider:     str
    service_category:   str
    account_id:         str
    environment:        str = "unknown"
    team:               str = "unknown"
    total_cost_usd:     float
    shap_values:        Dict[str, float]   # all feature SHAP values
    top_driver_1:       Optional[str]
    top_driver_1_value: Optional[float]
    top_driver_2:       Optional[str]
    top_driver_2_value: Optional[float]
    top_driver_3:       Optional[str]
    top_driver_3_value: Optional[float]
    model_r2_score:     Optional[float]
    feature_count:      Optional[int]
    computed_at:        Optional[datetime] = None

    class Config:
        json_encoders = {date: str, datetime: str}
