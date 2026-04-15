"""Pure unit tests for FeatureCalculator — NO DATABASE REQUIRED."""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from features.calculator import FeatureCalculator


@pytest.fixture
def calculator():
    return FeatureCalculator()


@pytest.fixture
def sample_df():
    """
    60 days of data: 2023-01-01 to 2023-03-01.
    Cost starts at 100.0 and increases by 2.0/day.
    Day 45 spikes to 500.0 (artificial anomaly).
    """
    dates = [date(2023, 1, 1) + timedelta(days=i) for i in range(60)]
    costs = [100.0 + 2.0 * i for i in range(60)]
    costs[44] = 500.0  # day 45 spike (index 44)

    return pd.DataFrame({
        "agg_date": dates,
        "cloud_provider": ["aws"] * 60,
        "service_category": ["compute"] * 60,
        "account_id": ["test-account"] * 60,
        "environment": ["prod"] * 60,
        "team": ["platform"] * 60,
        "total_cost_usd": costs,
        "record_count": [10] * 60,
    })


def test_all_feature_columns_present(calculator, sample_df):
    """Test 1: All feature columns are present after compute."""
    result = calculator.compute_features(sample_df)
    errors = calculator.validate_features(result)
    assert errors == [], f"Missing columns: {errors}"


def test_lag_features_correct(calculator, sample_df):
    """Test 2: Lag features have correct values."""
    result = calculator.compute_features(sample_df)

    # Row at index 1: cost_lag_1d == df.total_cost_usd[0]
    assert result.loc[1, "cost_lag_1d"] == sample_df["total_cost_usd"].iloc[0]

    # Row at index 7: cost_lag_7d == df.total_cost_usd[0]
    assert result.loc[7, "cost_lag_7d"] == sample_df["total_cost_usd"].iloc[0]

    # Row at index 0: cost_lag_1d is NaN (no prior data)
    assert pd.isna(result.loc[0, "cost_lag_1d"])


def test_rolling_mean_correct(calculator, sample_df):
    """Test 3: Rolling mean at index 6 matches manual calculation."""
    result = calculator.compute_features(sample_df)

    expected = sample_df["total_cost_usd"][:7].mean()
    actual = result.loc[6, "rolling_mean_7d"]
    assert abs(actual - expected) < 0.01, f"Expected {expected}, got {actual}"


def test_z_score_detects_spike(calculator, sample_df):
    """Test 4: Z-score detects the spike at day 45."""
    result = calculator.compute_features(sample_df)
    z = result.loc[44, "z_score_30d"]
    assert abs(z) > 2.0, f"Z-score {z} is too low for the spike"


def test_no_inf_values(calculator, sample_df):
    """Test 5: No inf values in output."""
    result = calculator.compute_features(sample_df)
    assert not result.isin([np.inf, -np.inf]).any().any(), "Found inf values"


def test_pct_change_zero_lag(calculator):
    """Test 6: pct_change is NaN when lag is 0."""
    dates = [date(2023, 1, 1) + timedelta(days=i) for i in range(5)]
    costs = [0.0, 0.0, 10.0, 20.0, 30.0]  # first two are 0

    df = pd.DataFrame({
        "agg_date": dates,
        "cloud_provider": ["aws"] * 5,
        "service_category": ["compute"] * 5,
        "account_id": ["test"] * 5,
        "environment": ["prod"] * 5,
        "team": ["eng"] * 5,
        "total_cost_usd": costs,
        "record_count": [1] * 5,
    })

    result = calculator.compute_features(df)
    # Row 2: cost=10, lag=0 -> pct_change should be NaN
    assert pd.isna(result.loc[2, "pct_change_1d"]), \
        f"Expected NaN, got {result.loc[2, 'pct_change_1d']}"


def test_calendar_features(calculator, sample_df):
    """Test 7: Calendar features are correctly computed."""
    result = calculator.compute_features(sample_df)

    # 2023-01-01 is a Sunday (dayofweek=6)
    assert result.loc[0, "day_of_week"] == 6
    assert result.loc[0, "is_weekend"] == True
    assert result.loc[0, "is_month_start"] == True

    # Find Jan 31 (index 30)
    assert result.loc[30, "is_month_end"] == True
