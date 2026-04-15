"""End-to-end feature pipeline test. Requires live TimescaleDB."""
import pytest
from datetime import date
from storage.db import DatabaseManager
from features.pipeline import FeatureEngineeringPipeline
from features.repository import FeatureRepository


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    DatabaseManager.initialize()
    if not DatabaseManager.health_check():
        pytest.skip("DB not reachable")

    # Ensure both tables exist
    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'spend_features'
                );
            """)
            if not cur.fetchone()[0]:
                pytest.skip("spend_features table does not exist")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'daily_aggregates'
                );
            """)
            if not cur.fetchone()[0]:
                pytest.skip("daily_aggregates table does not exist")
    yield
    DatabaseManager.close()


def test_full_pipeline_run():
    """Test 1: Full pipeline run for Jan 2023."""
    pipeline = FeatureEngineeringPipeline()
    result = pipeline.run(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 31)
    )
    assert result.features_written > 0, "No features written"
    assert result.groups_processed > 0, "No groups processed"
    assert result.errors == [], f"Pipeline errors: {result.errors}"


def test_features_queryable_after_pipeline():
    """Test 2: Features are queryable after pipeline run."""
    repo = FeatureRepository()
    rows = repo.get_features(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 31)
    )
    assert len(rows) > 0, "No features found after pipeline run"

    # Check rolling_mean_7d is populated (> 0 for non-zero-cost series)
    has_rolling = [r for r in rows if r.get("rolling_mean_7d") is not None
                   and r["rolling_mean_7d"] > 0]
    assert len(has_rolling) > 0, "No rows with rolling_mean_7d > 0"


def test_incremental_run():
    """Test 3: Incremental run completes (may write 0 if no recent data)."""
    pipeline = FeatureEngineeringPipeline()
    result = pipeline.run_incremental(days_back=7)
    # Just ensure it doesn't crash
    assert result.duration_seconds >= 0
