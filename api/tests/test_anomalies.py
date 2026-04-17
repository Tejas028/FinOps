import pytest

def test_list_anomalies(client):
    response = client.get("/anomalies?start_date=2023-01-01&end_date=2023-12-31")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    if data["total"] > 0:
        item = data["data"][0]
        assert "severity" in item
        assert "cloud_provider" in item
        assert "service" in item

def test_anomalies_summary(client):
    response = client.get("/anomalies/summary?start_date=2023-01-01&end_date=2023-12-31")
    assert response.status_code == 200
    data = response.json()
    assert "by_cloud" in data
    assert "by_severity" in data
    if data["total_anomalies"] > 0:
        assert "aws" in data["by_cloud"]
        # In synthetic data, we might only have low/medium/high
        assert any(k in data["by_severity"] for k in ["low", "medium", "high", "critical"])

def test_recent_anomalies(client):
    response = client.get("/anomalies/recent?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5

def test_anomaly_not_found(client):
    response = client.get("/anomalies/non-existent-id-123")
    assert response.status_code == 404
