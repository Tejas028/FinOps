import os
import joblib
import pandas as pd
import numpy as np
import lightgbm as lgb
from typing import List, Optional, Dict
from datetime import timedelta
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

from forecasting import config
from forecasting.models.base_model import BaseForecastModel, ForecastOutput

class LightGBMModel(BaseForecastModel):
    def __init__(self, cloud_provider: str = "", service: str = ""):
        super().__init__()
        self.cloud_provider = cloud_provider
        self.service = service
        self.models: Dict[int, lgb.LGBMRegressor] = {}
        self.residuals: Dict[int, float] = {}
        self.last_row: Optional[pd.DataFrame] = None
        self.last_date: Optional[pd.Timestamp] = None

    def fit(self, df: pd.DataFrame) -> dict:
        # Pre-process derive month and quarter
        df = df.copy()
        df['usage_date'] = pd.to_datetime(df['usage_date'])
        df['month'] = df['usage_date'].dt.month
        df['quarter'] = df['usage_date'].dt.quarter
        
        self.last_date = df['usage_date'].iloc[-1]
        
        # We must keep last_row (features of the last available day) to use in predict()
        features_only = df[config.LGBM_FEATURE_COLS].iloc[-1:]
        self.last_row = features_only

        mape_list = []
        mae_list = []

        for H in config.FORECAST_HORIZONS:
            df_h = df.copy()
            df_h['target'] = df_h['cost_usd'].shift(-H)
            df_h = df_h.dropna(subset=['target'])
            
            n = len(df_h)
            if n == 0:
                continue

            train_size = int(n * config.TRAIN_RATIO)
            val_size = int(n * config.VAL_RATIO)
            
            # Splitting Features and Target
            X = df_h[config.LGBM_FEATURE_COLS]
            y = df_h['target']
            
            X_train, y_train = X.iloc[:train_size], y.iloc[:train_size]
            X_val, y_val = X.iloc[train_size:train_size + val_size], y.iloc[train_size:train_size + val_size]
            X_test, y_test = X.iloc[train_size + val_size:], y.iloc[train_size + val_size:]

            model = lgb.LGBMRegressor(
                n_estimators=config.LGBM_N_ESTIMATORS,
                learning_rate=config.LGBM_LEARNING_RATE,
                num_leaves=config.LGBM_NUM_LEAVES,
                max_depth=config.LGBM_MAX_DEPTH,
                random_state=config.LGBM_RANDOM_STATE
            )
            
            # Using Early Stopping Callback
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                eval_metric=config.LGBM_EVAL_METRIC,
                callbacks=[lgb.early_stopping(stopping_rounds=config.LGBM_EARLY_STOPPING_ROUNDS, verbose=False)]
            )
            self.models[H] = model

            if len(X_test) > 0:
                y_pred = model.predict(X_test)
                residuals = y_test - y_pred
                std_residual = np.std(residuals)
                
                mae = mean_absolute_error(y_test, y_pred)
                mape = mean_absolute_percentage_error(y_test + 1e-9, y_pred)
                mape_list.append(mape)
                mae_list.append(mae)
            else:
                std_residual = 0.0

            self.residuals[H] = float(std_residual)

        mean_mape = np.mean(mape_list) if mape_list else 1.0
        mean_mae = np.mean(mae_list) if mae_list else 0.0

        self.metadata = {
            "model_type": "lightgbm",
            "test_mae": float(mean_mae),
            "test_mape": float(mean_mape)
        }
        return self.metadata

    def predict(self, horizon_days: int) -> List[ForecastOutput]:
        if self.last_row is None or not self.models:
            raise ValueError("Model is not fitted yet.")
            
        outputs = []
        # Predict uses last_row exactly as it is for all horizons
        for H in config.FORECAST_HORIZONS:
            if H > horizon_days:
                continue
            
            if H not in self.models:
                continue
                
            y_pred = self.models[H].predict(self.last_row)[0]
            std_res = self.residuals.get(H, 0.0)
            
            target_date = self.last_date + timedelta(days=H)
            
            lb = max(0.0, float(y_pred - 1.96 * std_res))
            ub = float(y_pred + 1.96 * std_res)
            
            outputs.append(ForecastOutput(
                cloud_provider=self.cloud_provider,
                service=self.service,
                horizon_days=H,
                forecast_date=target_date.date(),
                predicted_cost=float(y_pred),
                lower_bound=lb,
                upper_bound=ub,
                model_name="lightgbm"
            ))
            
        return outputs

    def save(self, path: str) -> None:
        if not self.models:
            return
            
        base_name = f"{self.cloud_provider}_{self.service}_lgbm"
        
        for H, model in self.models.items():
            model_path = os.path.join(path, f"{base_name}_h{H}.joblib")
            joblib.dump(model, model_path)
            
        meta_payload = {
            "metadata": self.metadata,
            "residuals": self.residuals,
            "last_row": self.last_row.to_dict(orient="records")[0] if self.last_row is not None else None,
            "last_date": self.last_date.isoformat() if self.last_date else None
        }
        meta_path = os.path.join(path, f"{base_name}_meta.joblib")
        joblib.dump(meta_payload, meta_path)

    def load(self, path: str) -> None:
        base_name = f"{self.cloud_provider}_{self.service}_lgbm"
        meta_path = os.path.join(path, f"{base_name}_meta.joblib")
        
        if os.path.exists(meta_path):
            meta_payload = joblib.load(meta_path)
            self.metadata = meta_payload["metadata"]
            self.residuals = meta_payload["residuals"]
            if meta_payload["last_row"]:
                self.last_row = pd.DataFrame([meta_payload["last_row"]])
            if meta_payload["last_date"]:
                self.last_date = pd.to_datetime(meta_payload["last_date"])
                
        for H in config.FORECAST_HORIZONS:
            model_path = os.path.join(path, f"{base_name}_h{H}.joblib")
            if os.path.exists(model_path):
                self.models[H] = joblib.load(model_path)
