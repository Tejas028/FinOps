import pytest
from datetime import date
from attribution.repository import AttributionRepository
from shared.schemas.attribution import AttributionRecord

@pytest.fixture
def repo():
    return AttributionRepository()

def test_get_all_groups(repo):
    groups = repo.get_all_groups()
    assert len(groups) > 0

def test_get_features_for_group(repo):
    feats = repo.get_features_for_group("aws", "other", date(2023, 1, 1), date(2023, 12, 31))
    assert isinstance(feats, list)
    if len(feats) > 0:
        # Check some columns exist
        sample = feats[0]
        assert "usage_date" in sample
        assert "cost_lag_1d" in sample
        assert "environment" in sample

def test_upsert_and_get_attributions(repo):
    # build custom attribution
    r1 = AttributionRecord(
        attribution_date=date(2023, 1, 1),
        cloud_provider="test_cloud",
        service_category="test_svc",
        account_id="acc123",
        environment="test",
        team="test_team",
        total_cost_usd=50.0,
        shap_values={"cost_lag_1d": 12.0, "rolling_mean_7d": 5.0},
        top_driver_1="cost_lag_1d",
        top_driver_1_value=12.0,
        top_driver_2="rolling_mean_7d",
        top_driver_2_value=5.0,
        top_driver_3=None,
        top_driver_3_value=None,
        model_r2_score=0.99,
        feature_count=2
    )
    
    written = repo.upsert_attributions([r1])
    assert written == 1
    
    # get_attributions
    fetched = repo.get_attributions(date(2023, 1, 1), date(2023, 1, 1), "test_cloud", "test_svc")
    assert len(fetched) == 1
    assert fetched[0].top_driver_1 == "cost_lag_1d"
    
    # filter test
    fetched_driver = repo.get_attributions(date(2023, 1, 1), date(2023, 1, 1), top_driver="cost_lag_1d")
    assert any(f.cloud_provider == "test_cloud" for f in fetched_driver)
    
    # upsert conflict test
    r1.total_cost_usd = 60.0
    repo.upsert_attributions([r1])
    
    fetched_updated = repo.get_attributions(date(2023, 1, 1), date(2023, 1, 1), "test_cloud", "test_svc")
    assert len(fetched_updated) == 1
    assert fetched_updated[0].total_cost_usd == 60.0 # Conflict correctly resolved via DO UPDATE SET
