import pytest

def test_list_attributions(client):
    response = client.get("/attribution?start_date=2023-01-01&end_date=2023-12-31")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    if data["total"] > 0:
        item = data["data"][0]
        assert "top_driver_1" in item
        assert "shap_values" in item

def test_top_drivers_aggregation(client):
    response = client.get("/attribution/top-drivers?start_date=2023-01-01&end_date=2023-12-31")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "driver" in item
        assert "avg_shap_value" in item
        assert "appearance_count" in item
        # top driver should be z_score_30d based on our data check
        assert data[0]["driver"] == "z_score_30d"

def test_group_series(client):
    response = client.get("/attribution/aws/other?start_date=2023-01-01&end_date=2023-12-31")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert data[0]["cloud_provider"] == "aws"
        assert data[0]["service_category"] == "other"
