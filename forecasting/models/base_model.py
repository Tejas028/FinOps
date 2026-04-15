from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
import pandas as pd

class ForecastOutput(BaseModel):
    cloud_provider: str
    service: str
    horizon_days: int
    forecast_date: date        # the future date being predicted
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    model_name: str            # "prophet" | "lightgbm"

class BaseForecastModel(ABC):
    def __init__(self):
        self.metadata = {}

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> dict:
        """
        Train on df. df has columns: usage_date, cost_usd (aggregated).
        Returns training metadata dict:
        {model, train_size, val_size, test_size, test_mae, test_mape}
        Time-ordered split: train=70%, val=15%, test=15%.
        """

    @abstractmethod
    def predict(self, horizon_days: int) -> List[ForecastOutput]:
        """
        Generate predictions for each future date in horizon.
        Called after fit(). Returns one ForecastOutput per future date.
        """

    @abstractmethod
    def save(self, path: str) -> None: ...

    @abstractmethod
    def load(self, path: str) -> None: ...
