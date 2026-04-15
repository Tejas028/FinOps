from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from .billing import CloudProvider

class ForecastResult(BaseModel):
    forecast_id: str
    cloud_provider: CloudProvider
    service: str
    region: Optional[str] = None
    horizon_days: int                          # 7, 14, 30, 90
    forecast_date: date
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    model_used: str                           # "prophet" | "lightgbm" | "ensemble"
    generated_at: datetime
