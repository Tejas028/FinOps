import pytest
from datetime import date
from storage.db import DatabaseManager
from alerting.engine import AlertingEngine
from alerting.repository import AlertRepository

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    DatabaseManager.initialize()
    # Ensure there is some data clean up if needed, 
    # but we will just test engine runs without side-effects ruining other tests.
    yield
    DatabaseManager.close()

def test_engine_run_and_dedup():
    engine = AlertingEngine()
    
    # Test 1: First run with wide date range
    start_date = date(2023, 1, 1)
    end_date = date(2023, 12, 31)
    
    res1 = engine.run(start_date, end_date)
    assert res1['total_inserted'] >= 0
    # Expected anomaly alerts > 0 because anomalies table has data
    assert res1['anomaly_alerts'] > 0
    
    # Test 2: Re-run same range -> total_skipped == total from Test 1
    res2 = engine.run(start_date, end_date)
    assert res2['total_inserted'] == 0
    # Since we deduplicate internally and externally, skipped should equal the alerts found
    assert res2['total_skipped'] == res1['anomaly_alerts'] + res1['spend_spike_alerts']

def test_engine_run_with_low_budget():
    engine = AlertingEngine()
    start_date = date(2023, 1, 1)
    end_date = date(2023, 12, 31)
    
    # Very low budget should trigger budget alerts
    res = engine.run(start_date, end_date, monthly_budget_usd=1000.0)
    assert res['budget_alerts'] > 0

def test_get_alerts_summary():
    repo = AlertRepository()
    start_date = date(2023, 1, 1)
    end_date = date(2023, 12, 31)
    # The summary endpoint logic inside API uses DatabaseManager directly
    # But repo has get_unresolved_count
    counts = repo.get_unresolved_count(start_date, end_date)
    assert isinstance(counts, dict)
    assert "low" in counts
    assert "critical" in counts
