import pytest
from datetime import date
from alerting.rules import AlertRulesEngine
from shared.schemas.alert import Alert

def test_evaluate_anomaly_critical():
    engine = AlertRulesEngine()
    anomaly = {
        "severity": "critical",
        "service": "compute",
        "usage_date": "2023-10-01",
        "deviation_pct": 150.0,
        "actual_cost": 250.0,
        "expected_cost": 100.0,
        "z_score": 4.5,
        "detection_method": "zscore",
        "cloud_provider": "aws",
        "account_id": "acc-123"
    }
    
    alert = engine.evaluate_anomaly(anomaly, {})
    assert alert is not None
    assert alert.alert_type == "anomaly_detected"
    assert alert.severity == "critical"
    assert alert.cloud_provider == "aws"
    assert "compute spend spike" in alert.title
    assert "150.0%" in alert.message

def test_evaluate_anomaly_low():
    engine = AlertRulesEngine()
    anomaly = {
        "severity": "low",
        "service": "storage",
        "usage_date": "2023-10-01",
        "deviation_pct": 10.0,
        "actual_cost": 110.0,
        "expected_cost": 100.0
    }
    alert = engine.evaluate_anomaly(anomaly, {})
    assert alert is not None
    assert alert.severity == "low"
    assert alert.alert_type == "anomaly_detected"
    assert "storage spend spike" in alert.title

def test_evaluate_spend_spike_high():
    engine = AlertRulesEngine()
    feature_row = {
        "pct_change_1d": 120.0,
        "cloud_provider": "azure",
        "service_category": "db",
        "feature_date": "2023-10-01"
    }
    alert = engine.evaluate_spend_spike(feature_row)
    assert alert is not None
    assert alert.alert_type == "spend_spike"
    assert alert.severity == "high"
    assert "120%" in alert.title

def test_evaluate_spend_spike_medium():
    engine = AlertRulesEngine()
    feature_row = {
        "pct_change_1d": 60.0
    }
    alert = engine.evaluate_spend_spike(feature_row)
    assert alert is not None
    assert alert.severity == "medium"

def test_evaluate_spend_spike_none():
    engine = AlertRulesEngine()
    feature_row = {
        "pct_change_1d": 10.0
    }
    alert = engine.evaluate_spend_spike(feature_row)
    assert alert is None

def test_evaluate_budget_breach_high():
    engine = AlertRulesEngine()
    alert = engine.evaluate_budget_breach("aws", 95000, 100000, "2023-10-25")
    assert alert is not None
    assert alert.alert_type == "budget_breach_imminent"
    assert alert.severity == "high"
    assert "budget at 95% - breach risk" in alert.title

def test_evaluate_budget_breach_critical():
    engine = AlertRulesEngine()
    alert = engine.evaluate_budget_breach("gcp", 105000, 100000, "2023-10-20")
    assert alert is not None
    assert alert.severity == "critical"
    assert "budget breach projected by 2023-10-20" in alert.title

def test_evaluate_budget_breach_none():
    engine = AlertRulesEngine()
    alert = engine.evaluate_budget_breach("aws", 50000, 100000, "2023-10-25")
    assert alert is None
