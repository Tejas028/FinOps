import lightgbm as lgb
import shap
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.metrics import r2_score
from attribution.config import *

class AttributionModel:
    """
    Per-(cloud x service_category) LightGBM regressor.
    Trained on spend_features. SHAP explains each prediction.
    """

    def __init__(self, cloud_provider: str, service_category: str):
        self.cloud_provider = cloud_provider
        self.service_category = service_category
        self.model = None
        self.explainer = None
        self.r2_score_ = None
        self._model_path = os.path.join(
            MODEL_REGISTRY_PATH,
            f"{cloud_provider}__{service_category}.joblib"
        )
        self._explainer_path = os.path.join(
            MODEL_REGISTRY_PATH,
            f"{cloud_provider}__{service_category}__explainer.joblib"
        )

    def fit(self, df: pd.DataFrame) -> dict:
        """
        Input df: rows from spend_features for this group,
                  sorted by usage_date ASC, NaN-filled.
        """
        X = df[SHAP_FEATURE_COLUMNS].copy()
        y = df[TARGET_COLUMN].copy()
        
        # SHAP doesn't like NaN
        X = X.fillna(0.0)

        n = len(df)
        train_size = int(n * TRAIN_RATIO)
        val_size = int(n * VAL_RATIO)
        test_size = n - train_size - val_size

        X_train, y_train = X.iloc[:train_size], y.iloc[:train_size]
        X_val, y_val = X.iloc[train_size:train_size + val_size], y.iloc[train_size:train_size + val_size]
        X_test, y_test = X.iloc[train_size + val_size:], y.iloc[train_size + val_size:]

        train_set = lgb.Dataset(X_train, label=y_train)
        valid_sets = [lgb.Dataset(X_val, label=y_val, reference=train_set)]

        self.model = lgb.train(
            params=LGBM_PARAMS,
            train_set=train_set,
            valid_sets=valid_sets,
            callbacks=[
                lgb.early_stopping(stopping_rounds=LGBM_PARAMS.get("early_stopping_rounds", 20), verbose=False)
            ]
        )

        best_iteration = self.model.best_iteration

        y_pred = self.model.predict(X_test, num_iteration=best_iteration)
        if len(y_test) > 1:
            self.r2_score_ = float(r2_score(y_test, y_pred))
        else:
            self.r2_score_ = 0.0

        # Build SHAP Explainer
        self.explainer = shap.TreeExplainer(self.model)

        # Save artifacts
        joblib.dump(self.model, self._model_path)
        joblib.dump(self.explainer, self._explainer_path)

        return {
            "r2": self.r2_score_,
            "best_iteration": best_iteration,
            "train_rows": train_size,
            "test_rows": test_size
        }

    def explain(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute SHAP values for all rows in df.
        """
        X = df[SHAP_FEATURE_COLUMNS].copy().fillna(0.0)
        shap_matrix = self.explainer.shap_values(X)
        
        result_df = pd.DataFrame(shap_matrix, columns=SHAP_FEATURE_COLUMNS, index=df.index)
        result_df[TARGET_COLUMN] = df[TARGET_COLUMN].values
        
        if 'usage_date' in df.columns:
            result_df['usage_date'] = df['usage_date'].values
            
        return result_df

    def load(self) -> bool:
        """
        Load saved model + explainer from registry.
        """
        if os.path.exists(self._model_path) and os.path.exists(self._explainer_path):
            try:
                self.model = joblib.load(self._model_path)
                self.explainer = joblib.load(self._explainer_path)
                # Since we don't save r2 globally in the object separately, we assign a placeholder or derive if needed
                # Realistically engine gets R2 from fit() or just skips it. We'll set a default if loaded
                self.r2_score_ = 0.0 
                return True
            except Exception as e:
                print(f"Failed to load model {self._model_path}: {e}")
                return False
        return False

    def extract_top_drivers(self, shap_row: pd.Series, n: int = 3) -> list:
        """
        Given a Series of feature -> shap_value for one row,
        return top N by absolute value.
        """
        # Filter for just feature columns
        driver_items = []
        for col in SHAP_FEATURE_COLUMNS:
            if col in shap_row:
                driver_items.append({"feature": col, "value": float(shap_row[col])})
                
        # Sort descending by absolute value
        driver_items.sort(key=lambda x: abs(x["value"]), reverse=True)
        return driver_items[:n]
