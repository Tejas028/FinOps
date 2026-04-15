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
    yield
    DatabaseManager.close()

def test_refresh_daily_aggregates_populates_table():
    client = StorageClient()
    # Insert dummy
    recs = [NormalizedRecord(
            fingerprint=f"agg_aws_{i}",
            cloud_provider="aws",
            account_id="acc",
            service_name_raw="test",
            service_category="compute",
            region="us-east",
            resource_id=None,
            usage_date=date(2023, 1, 20),
            cost_original=10.0,
            currency_original="USD",
            cost_usd=10.0,
            tags_raw="",
            tags={}
        ) for i in range(10)]
    
    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM billing_records WHERE usage_date = '2023-01-20' AND fingerprint LIKE 'agg_%'")
            cur.execute("DELETE FROM daily_aggregates WHERE agg_date = '2023-01-20'")
            
    client.upsert_records(recs)
    inserted = client.refresh_daily_aggregates(date(2023, 1, 20), date(2023, 1, 20))
    
    assert inserted > 0
    
    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM daily_aggregates WHERE agg_date = '2023-01-20'")
            assert cur.fetchone()[0] > 0

def test_aggregate_values_are_correct():
    client = StorageClient()
    aggs = client.get_daily_aggregates(date(2023, 1, 20), date(2023, 1, 20), cloud_provider="aws", service_category="compute")
    
    assert len(aggs) > 0
    row = next((a for a in aggs if a["cloud_provider"] == "aws" and a["service_category"] == "compute" and a["agg_date"] == date(2023, 1, 20)), None)
    
    assert row is not None
    assert row["total_cost"] >= 100.0  # 10 records * 10
    assert row["total_records"] >= 10

def test_idempotent_refresh():
    client = StorageClient()
    aggs = client.get_daily_aggregates(date(2023, 1, 20), date(2023, 1, 20), cloud_provider="aws", service_category="compute")
    initial_cost = aggs[0]["total_cost"]
    
    # Run again
    client.refresh_daily_aggregates(date(2023, 1, 20), date(2023, 1, 20))
    
    aggs_post = client.get_daily_aggregates(date(2023, 1, 20), date(2023, 1, 20), cloud_provider="aws", service_category="compute")
    assert aggs_post[0]["total_cost"] == initial_cost
