import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from detection.detectors.zscore_detector import ZScoreDetector


@pytest.fixture
def detector():
    return ZScoreDetector()


@pytest.fixture
def sample_df():
    rows = []
    for i in range(10):
        rows.append({
            "record_id": f"rec_{i}",
            "feature_date": date(2023, 6, 1) + timedelta(days=i),
            "cloud_provider": "aws",
            "service_category": "compute",
            "account_id": "acct-001",
            "total_cost_usd": 100.0 + i * 5,
            "rolling_mean_30d": 100.0,
            "z_score_30d": [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 0.5, -1.0, 0.0][i],
        })
    return pd.DataFrame(rows)


def test_high_zscore_high_score(detector, sample_df):
    results = detector.predict(sample_df)
    # z=5.0 (index 6) should have raw_score > 0.9
    assert results[6].raw_score > 0.9


def test_low_zscore_low_score(detector, sample_df):
    results = detector.predict(sample_df)
    # z=1.5 (index 0) should have raw_score < 0.3
    assert results[0].raw_score <= 0.01


def test_expected_cost_equals_rolling_mean(detector, sample_df):
    results = detector.predict(sample_df)
    assert results[0].expected_cost == 100.0


def test_deviation_pct_correct(detector, sample_df):
    results = detector.predict(sample_df)
    # Row 0: actual=100, expected=100 -> deviation=0%
    assert abs(results[0].deviation_pct) < 0.01
    # Row 5: actual=125, expected=100 -> deviation=25%
    assert abs(results[5].deviation_pct - 25.0) < 0.01


def test_nan_zscore_handled(detector):
    df = pd.DataFrame([{
        "record_id": "nan_test",
        "feature_date": date(2023, 1, 1),
        "cloud_provider": "aws",
        "service_category": "compute",
        "account_id": "acct",
        "total_cost_usd": 100.0,
        "rolling_mean_30d": 90.0,
        "z_score_30d": float("nan"),
    }])
    results = detector.predict(df)
    assert results[0].raw_score == 0.0
