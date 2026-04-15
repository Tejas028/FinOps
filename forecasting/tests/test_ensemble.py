import pytest
from datetime import date
from forecasting.models.ensemble import EnsembleForecaster
from forecasting.models.base_model import ForecastOutput
from shared.schemas.forecast import ForecastResult

def mock_output(pred, lb, ub, model_name, h=7):
    return ForecastOutput(
        cloud_provider="aws",
        service="ec2",
        horizon_days=h,
        forecast_date=date(2023, 2, 1),
        predicted_cost=pred,
        lower_bound=lb,
        upper_bound=ub,
        model_name=model_name
    )

def test_ensemble_weighting():
    ensemble = EnsembleForecaster()
    
    p_outputs = [mock_output(100.0, 90.0, 110.0, "prophet", 7)]
    l_outputs = [mock_output(120.0, 115.0, 125.0, "lightgbm", 7)]
    
    # prophet maps = 10%, lgbm mape = 5%
    # total = 15. prophet_wt = 5/15 = 1/3. lgbm_wt = 10/15 = 2/3.
    frs, metas = ensemble.blend(p_outputs, l_outputs, 0.10, 0.05)
    
    assert len(frs) == 1
    fr = frs[0]
    meta = metas[0]
    
    assert meta["prophet_weight"] < meta["lgbm_weight"]
    assert abs(meta["prophet_weight"] - (1/3)) < 1e-5
    
    # Check bounds
    assert fr.lower_bound == min(90.0, 115.0)  # 90.0
    assert fr.upper_bound == max(110.0, 125.0) # 125.0
    assert fr.model_used == "ensemble"

def test_single_model_fallback():
    ensemble = EnsembleForecaster()
    # Prophet natively outputs day 1 to day H. So we should provide it.
    p_outputs = []
    from datetime import timedelta
    for i in range(1, 8):
        # We need day 1 to be 2023-01-26, so day 7 is 2023-02-01
        po = mock_output(100.0, 90.0, 110.0, "prophet", 7)
        po.forecast_date = date(2023, 1, 25) + timedelta(days=i)
        p_outputs.append(po)
        
    l_outputs = []
    
    frs, metas = ensemble.blend(p_outputs, l_outputs, 0.10, 0.05)
    
    assert len(frs) == 1
    assert metas[0]["prophet_weight"] == 1.0
    assert metas[0]["lgbm_weight"] == 0.0
