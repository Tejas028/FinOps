import json
import os
import pandas as pd
import numpy as np
from typing import List, Optional
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from pydantic import ValidationError

from forecasting import config
from forecasting.models.base_model import BaseForecastModel, ForecastOutput

class ProphetModel(BaseForecastModel):
    def __init__(self, cloud_provider: str = "", service: str = ""):
        super().__init__()
        self.cloud_provider = cloud_provider
        self.service = service
        self.model: Optional[Prophet] = None

    def fit(self, df: pd.DataFrame) -> dict:
        # Time-ordered split 70/15/15
        n = len(df)
        train_size = int(n * config.TRAIN_RATIO)
        val_size = int(n * config.VAL_RATIO)
        test_size = n - train_size - val_size  # handle remainder

        # Rename for prophet
        pdf = df[['usage_date', 'cost_usd']].rename(columns={'usage_date': 'ds', 'cost_usd': 'y'}).copy()
        
        train_df = pdf.iloc[:train_size]
        test_df = pdf.iloc[train_size+val_size:] # Prophet typically does just train/test or cross-val, we use test directly since no hyperopt here

        self.model = Prophet(
            changepoint_prior_scale=config.PROPHET_CHANGEPOINT_PRIOR_SCALE,
            seasonality_prior_scale=config.PROPHET_SEASONALITY_PRIOR_SCALE,
            yearly_seasonality=config.PROPHET_YEARLY_SEASONALITY,
            weekly_seasonality=config.PROPHET_WEEKLY_SEASONALITY,
            daily_seasonality=config.PROPHET_DAILY_SEASONALITY,
            interval_width=config.PROPHET_INTERVAL_WIDTH,
            mcmc_samples=config.PROPHET_MCMC_SAMPLES
        )
        
        self.model.fit(train_df)

        # Evaluate on test set
        test_fcst = self.model.predict(test_df[['ds']])
        y_true = test_df['y'].values
        y_pred = test_fcst['yhat'].values
        
        # Avoid division by zero in MAPE if true cost is 0
        mae = mean_absolute_error(y_true, y_pred)
        # Add epsilon to y_true to prevent inf MAPE cleanly
        mape = mean_absolute_percentage_error(y_true + 1e-9, y_pred)

        # RETRAIN ON FULL DATASET before making final predictions
        # This ensures the "future" starts at the actual end of the available data.
        self.model = Prophet(
            changepoint_prior_scale=config.PROPHET_CHANGEPOINT_PRIOR_SCALE,
            seasonality_prior_scale=config.PROPHET_SEASONALITY_PRIOR_SCALE,
            yearly_seasonality=config.PROPHET_YEARLY_SEASONALITY,
            weekly_seasonality=config.PROPHET_WEEKLY_SEASONALITY,
            daily_seasonality=config.PROPHET_DAILY_SEASONALITY,
            interval_width=config.PROPHET_INTERVAL_WIDTH,
            mcmc_samples=config.PROPHET_MCMC_SAMPLES
        )
        self.model.fit(pdf)

        self.metadata = {
            "model_type": "prophet",
            "train_size": train_size,
            "val_size": val_size,
            "test_size": test_size,
            "test_mae": float(mae),
            "test_mape": float(mape)
        }
        return self.metadata

    def predict(self, horizon_days: int) -> List[ForecastOutput]:
        if not self.model:
            raise ValueError("Model is not fitted yet.")

        future = self.model.make_future_dataframe(periods=horizon_days, freq='D', include_history=False)
        forecast = self.model.predict(future)

        outputs = []
        for _, row in forecast.iterrows():
            pred = float(row['yhat'])
            lb = max(0.0, float(row['yhat_lower']))
            ub = float(row['yhat_upper'])
            
            outputs.append(ForecastOutput(
                cloud_provider=self.cloud_provider,
                service=self.service,
                horizon_days=horizon_days,
                forecast_date=row['ds'].date(),
                predicted_cost=pred,
                lower_bound=lb,
                upper_bound=ub,
                model_name="prophet"
            ))
        return outputs

    def save(self, path: str) -> None:
        if not self.model:
            return
        base_name = f"{self.cloud_provider}_{self.service}_prophet"
        model_path = os.path.join(path, f"{base_name}.json")
        meta_path = os.path.join(path, f"{base_name}_meta.json")
        
        with open(model_path, 'w') as f:
            json.dump(model_to_json(self.model), f)
            
        with open(meta_path, 'w') as f:
            json.dump(self.metadata, f)

    def load(self, path: str) -> None:
        base_name = f"{self.cloud_provider}_{self.service}_prophet"
        model_path = os.path.join(path, f"{base_name}.json")
        meta_path = os.path.join(path, f"{base_name}_meta.json")

        if os.path.exists(model_path):
            with open(model_path, 'r') as f:
                self.model = model_from_json(json.load(f))
        
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                self.metadata = json.load(f)
