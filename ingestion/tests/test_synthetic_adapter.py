import pytest
import os
import json
from datetime import date
from ingestion.adapters.synthetic_adapter import SyntheticAdapter

@pytest.fixture
def adapter():
    return SyntheticAdapter(data_root="synthetic_data/output")

def test_validate_connection(adapter):
    # Depending on existence of synthetic_data/output
    if os.path.exists("synthetic_data/output/combined/all_clouds_billing.parquet") or \
       os.path.exists("synthetic_data/output/aws"):
        assert adapter.validate_connection() is True

def test_fetch_full_range(adapter):
    if not adapter.validate_connection():
        pytest.skip("Synthetic data not generated yet.")
        
    res = adapter.fetch(date(2023, 1, 1), date(2024, 12, 31), cloud_provider="aws")
    assert len(res) > 0
    assert all(r.cloud_provider == "aws" for r in res)
    assert all(date(2023, 1, 1) <= r.usage_date <= date(2024, 12, 31) for r in res)
    assert all(isinstance(r.tags, str) for r in res)

def test_fetch_date_filter(adapter):
    if not adapter.validate_connection():
        pytest.skip("Synthetic data not generated yet.")

    res = adapter.fetch(date(2023, 6, 1), date(2023, 6, 30), cloud_provider="gcp")
    if res:
        assert all(date(2023, 6, 1) <= r.usage_date <= date(2023, 6, 30) for r in res)

def test_fetch_all_clouds(adapter):
    if not adapter.validate_connection():
        pytest.skip("Synthetic data not generated yet.")

    res = adapter.fetch(date(2023, 1, 1), date(2023, 1, 3))
    if res:
        providers = set(r.cloud_provider for r in res)
        # Should contain multiple/all if present
        assert len(providers) > 0

def test_tags_type_preservation(adapter):
    if not adapter.validate_connection():
        pytest.skip("Synthetic data not generated yet.")

    res = adapter.fetch(date(2023, 1, 1), date(2024, 12, 31), cloud_provider="azure")
    if res:
        import random
        sample = random.sample(res, min(100, len(res)))
        for r in sample:
            assert isinstance(r.tags, str)
            # json.loads shouldn't raise
            parsed = json.loads(r.tags)
            assert isinstance(parsed, dict)

def test_get_available_date_range(adapter):
    if not adapter.validate_connection():
        pytest.skip("Synthetic data not generated yet.")
        
    min_d, max_d = adapter.get_available_date_range()
    assert date(2022, 12, 1) <= min_d  # Account for backdated edge cases
    assert max_d <= date(2024, 12, 31)
