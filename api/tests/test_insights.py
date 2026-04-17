import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.routers.insights import _cache_key, _explain_feature
from api import config

client = TestClient(app)

def test_feature_explanation_mapping():
    assert _explain_feature("cost_lag_1d") == "yesterday's cost level"
    assert _explain_feature("rolling_mean_7d") == "7-day average spend"
    assert _explain_feature("unknown_feature") == "unknown feature"

def test_insight_cache_key():
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}
    assert _cache_key(data1) == _cache_key(data2)

def test_attribution_insight_no_api_key(monkeypatch):
    monkeypatch.setattr("api.routers.insights.GROQ_API_KEY", "")
    payload = {
        "cloud_provider": "aws",
        "service_category": "ec2",
        "date": "2023-01-01",
        "total_cost_usd": 100.0,
        "shap_values": {},
        "top_driver_1": "cost_lag_1d",
        "top_driver_1_value": 10.0
    }
    response = client.post("/insights/attribution", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False
    assert "not configured" in data["insight"]

def test_anomaly_insight_no_api_key(monkeypatch):
    monkeypatch.setattr("api.routers.insights.GROQ_API_KEY", "")
    payload = {
        "cloud_provider": "aws",
        "service": "ec2",
        "date": "2023-01-01",
        "actual_cost": 150.0,
        "expected_cost": 100.0,
        "deviation_pct": 50.0,
        "severity": "high",
        "detection_method": "zscore"
    }
    response = client.post("/insights/anomaly", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False

def test_daily_summary_no_api_key(monkeypatch):
    monkeypatch.setattr("api.routers.insights.GROQ_API_KEY", "")
    payload = {
        "date_range_start": "2023-01-01",
        "date_range_end": "2023-01-31",
        "total_spend": 5000.0,
        "anomaly_count": 5,
        "critical_count": 1,
        "high_count": 2,
        "forecast_30d": 6000.0,
        "by_cloud": {"aws": 5000.0},
        "unresolved_alerts": 3
    }
    response = client.post("/insights/daily-summary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False
