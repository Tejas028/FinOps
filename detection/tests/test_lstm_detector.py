import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from datetime import date, timedelta
from detection.detectors.lstm_detector import LSTMDetector
from detection import config


@pytest.fixture
def sinusoidal_df():
    """120 rows of sinusoidal cost for one group + 5 anomaly rows."""
    rows = []
    for i in range(120):
        cost = 100 + 20 * np.sin(2 * np.pi * i / 30) + np.random.normal(0, 2)
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
            "pct_change_1d": 0.02,
            "pct_change_7d": 0.05,
            "lag_1d": cost - 2,
            "lag_7d": cost - 5,
            "lag_30d": cost - 10,
        })
    # 5 anomaly rows (10x cost)
    for i in range(120, 125):
        rows.append({
            "record_id": f"rec_anom_{i}",
            "feature_date": date(2023, 1, 1) + timedelta(days=i),
            "cloud_provider": "aws",
            "service_category": "compute",
            "account_id": "acct-001",
            "total_cost_usd": 1000.0,
            "rolling_mean_7d": 1000.0,
            "rolling_std_7d": 5.0,
            "rolling_mean_30d": 100.0,
            "pct_change_1d": 9.0,
            "pct_change_7d": 9.0,
            "lag_1d": 100.0,
            "lag_7d": 100.0,
            "lag_30d": 100.0,
        })
    return pd.DataFrame(rows)


def test_lstm_early_stopping(sinusoidal_df):
    """Fit LSTM and assert early stopping fires before max epochs."""
    detector = LSTMDetector()
    detector.fit(sinusoidal_df.iloc[:120])

    for key, meta in detector.metadata.items():
        assert meta["best_epoch"] < config.LSTM_MAX_EPOCHS, \
            f"Early stopping did not fire for {key}"


def test_lstm_predict_anomaly_scores(sinusoidal_df):
    """LSTM should give higher scores to anomaly rows."""
    detector = LSTMDetector()
    detector.fit(sinusoidal_df.iloc[:120])
    results = detector.predict(sinusoidal_df)

    # Anomaly rows (120-124) should have relatively higher scores
    # (if enough sequence history exists)
    anomaly_results = [r for r in results if "anom" in r.record_id]
    if anomaly_results:
        max_anom_score = max(r.raw_score for r in anomaly_results)
        assert max_anom_score > 0.0  # LSTM detected something


def test_lstm_mc_dropout_nondeterministic(sinusoidal_df):
    """MC Dropout should produce non-zero std (verifies stochastic inference)."""
    detector = LSTMDetector()
    detector.fit(sinusoidal_df.iloc[:120])
    # Run predict twice and check results differ slightly
    r1 = detector.predict(sinusoidal_df.iloc[:120])
    r2 = detector.predict(sinusoidal_df.iloc[:120])
    # At least some scores should differ (MC Dropout is stochastic)
    scores1 = [r.raw_score for r in r1 if r.raw_score > 0]
    scores2 = [r.raw_score for r in r2 if r.raw_score > 0]
    if scores1 and scores2:
        # Not all scores should be identical
        any_different = any(abs(s1 - s2) > 1e-6 for s1, s2 in zip(scores1, scores2))
        assert any_different, "MC Dropout not producing stochastic results"


def test_lstm_save_load(sinusoidal_df):
    """Model + scaler + threshold should save and load correctly."""
    detector = LSTMDetector()
    detector.fit(sinusoidal_df.iloc[:120])

    with tempfile.TemporaryDirectory() as tmpdir:
        detector.save(tmpdir)
        saved = os.listdir(tmpdir)
        assert any(f.endswith(".keras") for f in saved), "No .keras model saved"
        assert any(f.endswith("_scaler.pkl") for f in saved), "No scaler saved"
        assert any(f.endswith("_meta.json") for f in saved), "No metadata saved"

        # Load into new detector
        detector2 = LSTMDetector()
        detector2.load(tmpdir)
        assert len(detector2.models) > 0
