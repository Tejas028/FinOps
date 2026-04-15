"""End-to-end detection engine test. Requires live TimescaleDB."""
import pytest
from datetime import date
from storage.db import DatabaseManager
from detection.engine import DetectionEngine


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    DatabaseManager.initialize()
    if not DatabaseManager.health_check():
        pytest.skip("DB not reachable")

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
                    WHERE table_name = 'anomalies'
                );
            """)
            if not cur.fetchone()[0]:
                pytest.skip("anomalies table does not exist")
    yield
    DatabaseManager.close()


def test_engine_train_predict():
    """Run engine on Jan-Mar 2023 AWS data."""
    engine = DetectionEngine(mode="train_predict")
    results = engine.run(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 3, 31),
        cloud_provider="aws",
        force_retrain=True,
    )
    assert len(results) > 0, "No anomalies detected"


def test_anomalies_written_to_db():
    """After detection, anomalies should exist in the DB."""
    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM anomalies WHERE cloud_provider = 'aws';")
            count = cur.fetchone()[0]
    assert count > 0, "No anomalies found in DB"
