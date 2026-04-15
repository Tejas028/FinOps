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

@pytest.fixture
def test_records():
    return [
        NormalizedRecord(
            fingerprint=f"test_fp_{i}",
            cloud_provider="aws",
            account_id="acc",
            service_name_raw="test",
            service_category="other",
            region="us-east",
            resource_id=None,
            usage_date=date(2023, 1, 15),
            cost_original=10.0,
            currency_original="USD",
            cost_usd=10.0,
            tags_raw="",
            tags={}
        ) for i in range(100)
    ]

def test_upsert_fresh_insert(test_records):
    client = StorageClient()
    
    # ensure clean state
    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM billing_records WHERE usage_date = '2023-01-15'")
            
    res = client.upsert_records(test_records)
    
    assert res.inserted == 100
    assert res.skipped == 0
    assert res.total == 100

def test_upsert_db_deduplication(test_records):
    client = StorageClient()
    # already inserted in previous test
    res = client.upsert_records(test_records)
    
    assert res.inserted == 0
    assert res.skipped == 100

def test_upsert_mixed_batch(test_records):
    client = StorageClient()
    
    # Make 50 new ones
    new_records = [
        NormalizedRecord(
            fingerprint=f"test_fp_new_{i}",
            cloud_provider="aws",
            account_id="acc",
            service_name_raw="test",
            service_category="other",
            region="us-east",
            resource_id=None,
            usage_date=date(2023, 1, 15),
            cost_original=10.0,
            currency_original="USD",
            cost_usd=10.0,
            tags_raw="",
            tags={}
        ) for i in range(50)
    ]
    
    # Total input: 50 existing (from test_records) + 50 new
    mixed = test_records[:50] + new_records
    res = client.upsert_records(mixed)
    
    assert res.inserted == 50
    assert res.skipped == 50

def test_batch_size_handling():
    client = StorageClient()
    massive = [
        NormalizedRecord(
            fingerprint=f"test_fp_massive_{i}",
            cloud_provider="aws",
            account_id="acc",
            service_name_raw="test",
            service_category="other",
            region="us-east",
            resource_id=None,
            usage_date=date(2023, 1, 15),
            cost_original=10.0,
            currency_original="USD",
            cost_usd=10.0,
            tags_raw="",
            tags={}
        ) for i in range(5000)
    ]
    
    res = client.upsert_records(massive)
    assert res.inserted == 5000
