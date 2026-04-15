import pytest
import pandas as pd
import numpy as np
from datetime import timedelta, date
import os
from forecasting.models.prophet_model import ProphetModel
from forecasting import config

def generate_prophet_data(n=120):
    start_date = date(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n)]
    # sinusoidal data
    costs = [100.0 + 10.0 * np.sin(2 * np.pi * i / 7) for i in range(n)]
    return pd.DataFrame({'usage_date': dates, 'cost_usd': costs})

@pytest.fixture
def clean_registry():
    path = config.MODEL_REGISTRY_PATH
    os.makedirs(path, exist_ok=True)
    yield path
    # optionally cleanup, but we can leave it

def test_prophet_fit_predict(clean_registry):
    df = generate_prophet_data(120)
    model = ProphetModel(cloud_provider="aws", service="test_svc")
    
    # test fit
    meta = model.fit(df)
    assert "test_mape" in meta
    assert meta["test_mape"] < 0.25  # Should be easily achievable on clean sine wave
    
    # test save
    model.save(clean_registry)
    expected_path = os.path.join(clean_registry, "aws_test_svc_prophet_meta.json")
    assert os.path.exists(expected_path)
    
    # test predict
    horizon = 30
    outputs = model.predict(horizon_days=horizon)
    assert len(outputs) == horizon
    
    # ensure no negative bounds
    for out in outputs:
        assert out.lower_bound >= 0.0
