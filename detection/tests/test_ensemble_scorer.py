import pytest
from datetime import date
from detection.detectors.base_detector import DetectorResult
from detection.ensemble.scorer import EnsembleScorer


@pytest.fixture
def scorer():
    return EnsembleScorer()


def _make_result(score, name="zscore"):
    return DetectorResult(
        record_id="rec_1", usage_date=date(2023, 1, 1),
        cloud_provider="aws", service="compute", account_id="acct",
        raw_score=score, expected_cost=100.0, actual_cost=150.0,
        deviation_pct=50.0, detector_name=name,
    )


def test_graceful_degradation_lstm_none(scorer):
    """If lstm_score=None, weights redistributed among zscore and iforest."""
    zr = _make_result(0.8, "zscore")
    ir = _make_result(0.6, "iforest")
    score = scorer.score(zr, ir, None)
    # Manual: zscore=0.3, iforest=0.35 -> total=0.65
    # Redistributed: zscore=0.3/0.65, iforest=0.35/0.65
    expected = 0.8 * (0.30/0.65) + 0.6 * (0.35/0.65)
    assert abs(score - expected) < 0.01


def test_severity_critical(scorer):
    assert scorer.map_severity(0.95) == "critical"


def test_severity_medium(scorer):
    assert scorer.map_severity(0.55) == "medium"


def test_below_threshold_returns_none(scorer):
    zr = _make_result(0.1)
    ir = _make_result(0.1)
    lr = _make_result(0.1)
    result = scorer.score_to_anomaly_result(
        {"total_cost_usd": 100, "cloud_provider": "aws",
         "service_category": "compute", "account_id": "acct",
         "feature_date": date(2023, 1, 1)},
        zr, ir, lr
    )
    assert result is None


def test_above_threshold_returns_anomaly_result(scorer):
    zr = _make_result(0.9)
    ir = _make_result(0.8)
    lr = _make_result(0.85)
    result = scorer.score_to_anomaly_result(
        {"total_cost_usd": 150, "cloud_provider": "aws",
         "service_category": "compute", "account_id": "acct",
         "feature_date": date(2023, 1, 1), "record_id": "test_rec"},
        zr, ir, lr
    )
    assert result is not None
    assert result.anomaly_id is not None
    assert result.detection_method == "ensemble"
    assert result.actual_cost == 150.0
