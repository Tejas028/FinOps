import pytest
from datetime import date
from storage.db import DatabaseManager
from storage.client import StorageClient
from shared.schemas.normalized import NormalizedRecord

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    DatabaseManager.initialize()
    if not DatabaseManager.health_check():
        pytest.skip("DB not reachable")
        
    # Setup test records
    client = StorageClient()
    recs = []
    
    # AWS compute
    for i in range(50):
        recs.append(NormalizedRecord(fingerprint=f"rq_aws_{i}", cloud_provider="aws", account_id="a", service_name_raw="", service_category="compute", region="r", usage_date=date(2023, 1, 5), cost_original=1.0, currency_original="U", cost_usd=1.0, tags_raw="", tags={}))
    
    # Azure storage
    for i in range(50):
        recs.append(NormalizedRecord(fingerprint=f"rq_az_{i}", cloud_provider="azure", account_id="a", service_name_raw="", service_category="storage", region="r", usage_date=date(2023, 1, 6), cost_original=1.0, currency_original="U", cost_usd=1.0, tags_raw="", tags={}))

    # GCP compute
    for i in range(100):
        recs.append(NormalizedRecord(fingerprint=f"rq_gc_{i}", cloud_provider="gcp", account_id="a", service_name_raw="", service_category="compute", region="r", usage_date=date(2023, 1, 15), cost_original=1.0, currency_original="U", cost_usd=1.0, tags_raw="", tags={}))

    
    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM billing_records WHERE fingerprint LIKE 'rq_%'")
            
    client.upsert_records(recs)
    yield
    DatabaseManager.close()

def test_get_records_date_range_filter():
    client = StorageClient()
    res = client.get_records(date(2023, 1, 1), date(2023, 1, 10))
    # Includes aws and azure, but not gcp (Jan 15)
    assert len(res) == 100
    assert all(date(2023, 1, 1) <= r.usage_date <= date(2023, 1, 10) for r in res)

def test_get_records_cloud_provider_filter():
    client = StorageClient()
    res = client.get_records(date(2023, 1, 1), date(2023, 1, 31), cloud_provider="aws")
    assert len(res) == 50
    assert all(r.cloud_provider == "aws" for r in res)

def test_get_records_service_category_filter():
    client = StorageClient()
    res = client.get_records(date(2023, 1, 1), date(2023, 1, 31), service_category="compute")
    # AWS + GCP = 150
    assert len(res) == 150
    assert all(r.service_category == "compute" for r in res)

def test_get_spend_summary():
    client = StorageClient()
    summary = client.get_spend_summary(date(2023, 1, 1), date(2023, 1, 31), group_by="cloud_provider")
    
    assert len(summary) >= 3
    aws_row = next(s for s in summary if s["cloud_provider"] == "aws")
    assert aws_row["total_cost"] >= 50.0

def test_get_record_count():
    client = StorageClient()
    c = client.get_record_count(date(2023, 1, 1), date(2023, 1, 10))
    assert c >= 100  # depends on if other tests ran, but at least 100
