"""DB integration tests for FeatureRepository. Requires live TimescaleDB."""
import pytest
from datetime import date
from storage.db import DatabaseManager
from features.repository import FeatureRepository


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    DatabaseManager.initialize()
    if not DatabaseManager.health_check():
        pytest.skip("DB not reachable")

    # Ensure spend_features table exists
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
    yield
    DatabaseManager.close()


def test_get_daily_aggregates_returns_data():
    """Test 1: get_daily_aggregates_for_features returns data."""
    repo = FeatureRepository()
    result = repo.get_daily_aggregates_for_features(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 31)
    )
    assert len(result) > 0
    required_keys = {"agg_date", "cloud_provider", "service_category",
                     "account_id", "total_cost_usd", "record_count"}
    assert required_keys.issubset(set(result[0].keys()))


def test_upsert_features_inserts_and_updates():
    """Test 2: upsert_features inserts and then updates correctly."""
    repo = FeatureRepository()

    # Clean up test rows first
    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM spend_features
                WHERE account_id = 'repo-test-acct'
                AND feature_date = '2023-06-15'
            """)

    test_features = []
    for i in range(10):
        test_features.append({
            "feature_date": date(2023, 6, 15),
            "cloud_provider": "aws",
            "service_category": f"svc_{i}",
            "account_id": "repo-test-acct",
            "environment": "prod",
            "team": "eng",
            "total_cost_usd": 100.0 + i,
            "record_count": 5,
            "cost_lag_1d": 99.0,
            "cost_lag_7d": 95.0,
            "cost_lag_30d": 80.0,
            "rolling_mean_7d": 98.0,
            "rolling_std_7d": 3.0,
            "rolling_mean_30d": 90.0,
            "rolling_std_30d": 5.0,
            "pct_change_1d": 0.01,
            "pct_change_7d": 0.05,
            "pct_change_30d": 0.25,
            "z_score_30d": 2.0,
            "day_of_week": 3,
            "day_of_month": 15,
            "week_of_year": 24,
            "month": 6,
            "is_weekend": False,
            "is_month_start": False,
            "is_month_end": False,
        })

    count = repo.upsert_features(test_features)
    assert count == 10

    # Update same rows with different cost
    for f in test_features:
        f["total_cost_usd"] = 999.0
    count2 = repo.upsert_features(test_features)
    assert count2 == 10

    # Verify DB values updated
    rows = repo.get_features(
        start_date=date(2023, 6, 15),
        end_date=date(2023, 6, 15),
        account_id="repo-test-acct"
    )
    assert all(r["total_cost_usd"] == 999.0 for r in rows)


def test_get_features_date_range_filter():
    """Test 3: get_features respects date range filter."""
    repo = FeatureRepository()
    rows = repo.get_features(
        start_date=date(2023, 6, 15),
        end_date=date(2023, 6, 15),
        account_id="repo-test-acct"
    )
    assert all(
        r["feature_date"] == date(2023, 6, 15) for r in rows
    )


def test_get_features_z_score_filter():
    """Test 4: get_features with min_z_score filter."""
    repo = FeatureRepository()
    rows = repo.get_features(
        start_date=date(2023, 6, 15),
        end_date=date(2023, 6, 15),
        min_z_score=2.0
    )
    assert all(abs(r["z_score_30d"]) >= 2.0 for r in rows)
