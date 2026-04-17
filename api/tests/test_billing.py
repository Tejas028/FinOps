import pytest

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db_connected"] is True

def test_billing_summary(client):
    response = client.get("/billing/summary?start_date=2023-01-01&end_date=2023-03-31")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert data["page"] == 1
    if len(data["data"]) > 0:
        item = data["data"][0]
        assert "total_cost_usd" in item
        assert "record_count" in item
        assert "anomaly_count" in item

def test_billing_by_cloud(client):
    response = client.get("/billing/by-cloud?start_date=2023-01-01&end_date=2023-12-31")
    assert response.status_code == 200
    data = response.json()
    # Should have aws, azure, gcp
    clouds = [item["dimension"] for item in data]
    assert "aws" in clouds
    # Total pct should be around 100
    total_pct = sum(item["pct_of_total"] for item in data)
    assert 99.9 <= total_pct <= 100.1

def test_billing_by_service(client):
    response = client.get("/billing/by-service?start_date=2023-01-01&end_date=2023-12-31&top_n=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5

def test_billing_trend(client):
    response = client.get("/billing/trend?start_date=2023-01-01&end_date=2023-03-31&granularity=month")
    assert response.status_code == 200
    data = response.json()
    # Jan, Feb, Mar 2023
    assert len(data) == 3
    assert "period" in data[0]
    assert "total_cost_usd" in data[0]

def test_invalid_date_range(client):
    response = client.get("/billing/summary?start_date=2023-12-31&end_date=2023-01-01")
    # This might return 200 with 0 data, or 422 if we had validation.
    # FastAPI date type handles format, but not logical range unless Pydantic validator is used.
    assert response.status_code == 200
    assert response.json()["total"] == 0
