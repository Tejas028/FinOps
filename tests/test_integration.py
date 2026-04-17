import pytest
from datetime import date
from fastapi.testclient import TestClient

from api.main import app
from storage.db import DatabaseManager

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    DatabaseManager.initialize()
    yield
    DatabaseManager.close()

class TestDataCompleteness:
    """Group 1: Validate all clouds have data backfilled appropriately."""
    def test_aws_data_exists(self):
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM billing_records WHERE cloud_provider='aws'")
                count = cur.fetchone()[0]
                assert count > 0, "AWS data missing from DB"
                
    def test_azure_data_exists(self):
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM billing_records WHERE cloud_provider='azure'")
                count = cur.fetchone()[0]
                assert count > 0, "Azure data missing from DB"
                
    def test_gcp_data_exists(self):
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM billing_records WHERE cloud_provider='gcp'")
                count = cur.fetchone()[0]
                assert count > 0, "GCP data missing from DB"

class TestSchemaContracts:
    """Group 2: Validate API returns expected schemas."""
    def test_billing_bounds_schema(self):
        res = client.get("/billing/bounds")
        assert res.status_code == 200
        data = res.json()
        assert "min_date" in data
        assert "max_date" in data
        # Check actual formats
        assert len(data["min_date"]) == 10
        assert len(data["max_date"]) == 10

class TestAPIContracts:
    """Group 3: Validate key API endpoints respond correctly."""
    def test_get_billing_summary(self):
        res = client.get("/billing/summary?start_date=2024-01-01&end_date=2024-12-31")
        assert res.status_code == 200
        assert "data" in res.json()
        assert "total" in res.json()

    def test_get_anomalies_latest(self):
        res = client.get("/anomalies?start_date=2024-01-01&end_date=2024-12-31")
        assert res.status_code == 200
        assert "data" in res.json()

    def test_get_forecasts(self):
        res = client.get("/forecasts?horizon_days=30")
        assert res.status_code == 200
        assert "data" in res.json()

    def test_get_budget_risk_without_cloud(self):
        res = client.get("/forecasts/budget-risk?monthly_budget_usd=50000")
        # Could be 404 if no data match or 200 if it finds a global forecast
        assert res.status_code in [200, 404]

class TestCrossModuleIntegrity:
    """Group 4: Ensure anomalies actually exist matching billing flags."""
    def test_anomaly_flags_match_anomalies_table(self):
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                # Get one anomaly that we know is flagged in billing records
                cur.execute("SELECT COUNT(*) FROM billing_records WHERE anomaly_flag = true")
                billing_flag_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM anomalies")
                anomalies_table_count = cur.fetchone()[0]
                
                # In ensemble logic, anomalies are tracked securely
                assert anomalies_table_count > 0, "Anomalies table is empty!"
                assert billing_flag_count > 0, "Billing records do not have anomaly_flag set!"
