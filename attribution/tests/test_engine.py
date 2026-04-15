import pytest
from datetime import date
from attribution.engine import AttributionEngine, AttributionEngineResult
from attribution.repository import AttributionRepository

@pytest.fixture
def repo():
    return AttributionRepository()

@pytest.fixture
def engine(repo):
    return AttributionEngine(repository=repo)

def test_engine_run(engine, repo):
    # Run a test interval on AWS only to map bounds
    result = engine.run(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        cloud_provider="aws",
        force_retrain=True
    )
    
    # we know 'aws_other' has more than 45 rows. So it should not be skipped.
    assert result.groups_processed > 0
    assert result.attributions_written > 0
    assert len(result.errors) == 0
    
    # We also know 'aws_svc_0' to 'aws_svc_9' have only 1 row. They should be skipped natively
    assert result.groups_skipped > 0

def test_engine_skipped(engine):
    # 2026 doesn't have data, everything returns empty, thus skipped
    result = engine.run(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        cloud_provider="aws"
    )
    # The groups count will still query `get_all_groups()`.
    # And then fetch individually, which returns 0 rows.
    assert result.groups_processed == 0
    assert result.groups_skipped > 0
    
def test_engine_retrain_flag(engine):
    # Running without force_retrain (should load saved model from the previous test)
    result = engine.run(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        cloud_provider="aws",
        force_retrain=False
    )
    # Should complete super fast because logic skips training
    assert result.groups_processed > 0
    assert len(result.errors) == 0
