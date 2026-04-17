from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
import uuid

class Alert(BaseModel):
    alert_id:        str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type:      str
    severity:        str
    cloud_provider:  str
    service_category: Optional[str]
    account_id:      Optional[str]
    alert_date:      date
    title:           str
    message:         str
    metadata:        Dict[str, Any] = {}
    is_resolved:     bool = False
    resolved_at:     Optional[datetime] = None
    created_at:      Optional[datetime] = None

    class Config:
        json_encoders = {date: str, datetime: str}
