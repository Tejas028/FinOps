import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from attribution.model import AttributionModel
from attribution.config import SHAP_FEATURE_COLUMNS, TARGET_COLUMN

def synthetic_dataframe(n=120) -> pd.DataFrame:
    start_date = date(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n)]
    
    # Baseline cost
    costs = np.zeros(n)
    
    df = pd.DataFrame({'usage_date': dates})
    
    # Generate all columns
    for col in SHAP_FEATURE_COLUMNS:
        # Give random gaussian to features
        df[col] = np.random.normal(0, 1, n)
        
    # Let's say cost_lag_1d drives the cost strongly + trend
    costs = 100 + df['cost_lag_1d'] * 50 + df['rolling_mean_7d'] * 20
    
    # spike at day 90
    if n >= 90:
        costs[90:95] *= 3
        
    df[TARGET_COLUMN] = costs
    return df

@pytest.fixture
def model():
    return AttributionModel(cloud_provider="test_cloud", service_category="test_svc")

@pytest.fixture
def test_df():
    return synthetic_dataframe(120)

def test_model_fit(model, test_df):
    result = model.fit(test_df)
    
    assert result["r2"] > 0, "R2 should be > 0"
    assert result["best_iteration"] <= 500
    
def test_model_explain(model, test_df):
    model.fit(test_df)
    shap_df = model.explain(test_df)
    
    # test 3: Returns dataframe with 1 row per input row
    assert len(shap_df) == len(test_df)
    for col in SHAP_FEATURE_COLUMNS:
        assert col in shap_df.columns
        
    # test 4: Sum of shap values + base value = f(x)
    # the base value config in lightgbm vs shap
    base_value = model.explainer.expected_value
    actual_pred = model.model.predict(test_df[SHAP_FEATURE_COLUMNS])
    
    # SHAP row sum
    shap_sum = shap_df[SHAP_FEATURE_COLUMNS].sum(axis=1) + base_value
    
    # Use np.allclose to assert near equality
    np.testing.assert_allclose(shap_sum, actual_pred, rtol=1e-3, atol=1e-3)
    
def test_extract_top_drivers(model):
    # Fake shap row
    shap_row = pd.Series({"cost_lag_1d": 15.5, "rolling_mean_7d": -42.2, "day_of_week": 2.1, "is_weekend": -0.5})
    drivers = model.extract_top_drivers(shap_row, n=3)
    
    assert len(drivers) == 3
    assert drivers[0]["feature"] == "rolling_mean_7d"
    assert drivers[0]["value"] == -42.2
    assert drivers[1]["feature"] == "cost_lag_1d"

def test_save_and_load(model, test_df):
    model.fit(test_df)
    
    new_model = AttributionModel(cloud_provider="test_cloud", service_category="test_svc")
    assert new_model.load() is True
    assert new_model.model is not None
    assert new_model.explainer is not None
