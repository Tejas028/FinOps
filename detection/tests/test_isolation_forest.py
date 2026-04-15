import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from detection.detectors.isolation_forest_detector import IsolationForestDetector
from detection import config
import tempfile
import os


@pytest.fixture
def normal_df():
    """100 rows of normal data + 5 outliers (5x cost)."""
    np.random.seed(42)
    rows = []
    for i in range(100):
        cost = 100 + np.random.normal(0, 5)
        rows.append({
            "record_id": f"rec_{i}",
            "feature_date": date(2023, 1, 1) + timedelta(days=i),
            "cloud_provider": "aws",
            "service_category": "compute",
            "account_id": "acct-001",
            "total_cost_usd": cost,
            "rolling_mean_7d": cost,
            "rolling_std_7d": 5.0,
            "rolling_mean_30d": 100.0,
            "rolling_std_30d": 5.0,
            "pct_change_1d": 0.02,
            "pct_change_7d": 0.05,
            "lag_1d": cost - 2,
            "lag_7d": cost - 5,
            "lag_30d": cost - 10,
            "day_of_week": i % 7,
            "is_month_end": False,
            "is_weekend": (i % 7) >= 5,
        })
    # Inject 5 outliers
    for i in range(100, 105):
        rows.append({
            "record_id": f"rec_{i}",
            "feature_date": date(2023, 1, 1) + timedelta(days=i),
            "cloud_provider": "aws",
            "service_category": "compute",
            "account_id": "acct-001",
            "total_cost_usd": 500.0,  # 5x cost
            "rolling_mean_7d": 500.0,
            "rolling_std_7d": 5.0,
            "rolling_mean_30d": 100.0,
            "rolling_std_30d": 5.0,
            "pct_change_1d": 9.0,
            "pct_change_7d": 9.0,
            "lag_1d": 100.0,
            "lag_7d": 100.0,
            "lag_30d": 100.0,
            "day_of_week": i % 7,
            "is_month_end": False,
            "is_weekend": (i % 7) >= 5,
        })
    return pd.DataFrame(rows)


def test_fit_and_predict(normal_df):
    detector = IsolationForestDetector()
    # Fit on first 80 rows (normal)
    detector.fit(normal_df.iloc[:80])
    # Predict on all
    results = detector.predict(normal_df)
    assert len(results) == 105

    # Outlier rows should have higher scores
    outlier_scores = [r.raw_score for r in results[100:]]
    normal_scores = [r.raw_score for r in results[:80]]
    assert np.mean(outlier_scores) > np.mean(normal_scores)


def test_model_checkpoint_saved(normal_df):
    detector = IsolationForestDetector()
    detector.fit(normal_df.iloc[:80])

    with tempfile.TemporaryDirectory() as tmpdir:
        detector.save(tmpdir)
        saved_files = os.listdir(tmpdir)
        assert any("iforest_" in f for f in saved_files)


def test_load_and_predict(normal_df):
    detector = IsolationForestDetector()
    detector.fit(normal_df.iloc[:80])

    with tempfile.TemporaryDirectory() as tmpdir:
        detector.save(tmpdir)
        detector2 = IsolationForestDetector()
        detector2.load(tmpdir)
        results = detector2.predict(normal_df)
        assert len(results) == 105
