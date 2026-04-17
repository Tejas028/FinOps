import pytest

def test_list_forecasts(client):
    response = client.get("/forecasts?cloud_provider=aws&horizon_days=30")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    if data["total"] > 0:
        assert data["data"][0]["horizon_days"] == 30

def test_forecast_latest(client):
    # AWS/other-category is a known group from previous logs
    response = client.get("/forecasts/latest?cloud_provider=aws&service=other&horizon_days=30")
    assert response.status_code == 200
    data = response.json()
    if len(data) > 0:
        # Check they all share the same generated_at
        gen_at = data[0]["generated_at"]
        for item in data:
            assert item["generated_at"] == gen_at
        # Check order
        dates = [item["forecast_date"] for item in data]
        assert dates == sorted(dates)

def test_budget_risk(client):
    response = client.get("/forecasts/budget-risk?cloud_provider=aws&monthly_budget_usd=180000")
    assert response.status_code == 200
    data = response.json()
    assert "breach_risk" in data
    assert data["breach_risk"] in ["none", "possible", "likely", "certain"]
    if data["breach_risk"] != "none":
        assert data["breach_date"] is not None
        assert data["days_to_breach"] is not None
