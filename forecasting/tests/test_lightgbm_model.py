import pytest
import pandas as pd
import numpy as np
from datetime import timedelta, date
import os
from forecasting.models.lightgbm_model import LightGBMModel
from forecasting import config

def generate_lgbm_data(n=120):
    start_date = date(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n)]
    costs = [100.0 + i * 0.5 + np.random.normal(0, 5) for i in range(n)]
    df = pd.DataFrame({'usage_date': dates, 'cost_usd': costs})
    
    # Needs LGBM_FEATURE_COLS
    for idx, col in enumerate(config.LGBM_FEATURE_COLS):
        if col not in ["month", "quarter"]:
            # Fill with random data for test
            df[col] = np.random.normal(10, 2, n)
            
    df['day_of_week'] = [d.weekday() for d in dates]
    df['is_weekend'] = [1 if d.weekday() >= 5 else 0 for d in dates]
    df['is_month_end'] = 0 # simplified
    return df

@pytest.fixture
def clean_registry():
    path = config.MODEL_REGISTRY_PATH
    os.makedirs(path, exist_ok=True)
    yield path

def test_lgbm_fit_predict(clean_registry):
    df = generate_lgbm_data(120)
    model = LightGBMModel(cloud_provider="aws", service="test_svc")
    
    meta = model.fit(df)
    assert meta["model_type"] == "lightgbm"
    
    # Assert early stopping fired by checking best_iteration if available
    for h, m in model.models.items():
        if hasattr(m, 'best_iteration_') and m.best_iteration_ is not None:
            assert m.best_iteration_ < config.LGBM_N_ESTIMATORS
            
    model.save(clean_registry)
    expected_path = os.path.join(clean_registry, "aws_test_svc_lgbm_h7.joblib")
    assert os.path.exists(expected_path)
    
    outputs = model.predict(horizon_days=90)
    # We expect 4 horizon outputs
    expected_horizons = [h for h in config.FORECAST_HORIZONS if h <= 90]
    assert len(outputs) == len(expected_horizons)
    
    for out in outputs:
        assert out.lower_bound >= 0.0
