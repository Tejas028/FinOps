from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class DetectorResult:
    """Lightweight output from any single detector."""
    record_id: str
    usage_date: date
    cloud_provider: str
    service: str
    account_id: str
    raw_score: float        # 0.0 to 1.0
    z_score: Optional[float] = None
    expected_cost: float = 0.0
    actual_cost: float = 0.0
    deviation_pct: float = 0.0
    detector_name: str = ""


class BaseDetector(ABC):
    @abstractmethod
    def fit(self, df: pd.DataFrame) -> None:
        """Train or calibrate the detector on historical data."""

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> List[DetectorResult]:
        """Run detection on df. Returns one DetectorResult per row."""

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist model state to disk."""

    @abstractmethod
    def load(self, path: str) -> None:
        """Load model state from disk."""
