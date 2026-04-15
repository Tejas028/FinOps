import pandas as pd
import numpy as np
from typing import List


class FeatureCalculator:
    """Pure feature computation logic. No database calls."""

    FEATURE_COLUMNS = [
        "feature_date", "cloud_provider", "service_category", "account_id",
        "environment", "team", "total_cost_usd", "record_count",
        "cost_lag_1d", "cost_lag_7d", "cost_lag_30d",
        "rolling_mean_7d", "rolling_std_7d", "rolling_mean_30d", "rolling_std_30d",
        "pct_change_1d", "pct_change_7d", "pct_change_30d",
        "z_score_30d",
        "day_of_week", "day_of_month", "week_of_year", "month",
        "is_weekend", "is_month_start", "is_month_end",
    ]

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Input: DataFrame sorted by agg_date ASC for ONE group.
        Output: Same DataFrame with all feature columns added.
        """
        df = df.copy()

        # Ensure agg_date is datetime for calendar features
        df["agg_date"] = pd.to_datetime(df["agg_date"])

        cost = df["total_cost_usd"]

        # ── Lag features ──
        df["cost_lag_1d"] = cost.shift(1)
        df["cost_lag_7d"] = cost.shift(7)
        df["cost_lag_30d"] = cost.shift(30)

        # ── Rolling statistics ──
        df["rolling_mean_7d"] = cost.rolling(7, min_periods=1).mean()
        df["rolling_std_7d"] = cost.rolling(7, min_periods=1).std()
        df["rolling_mean_30d"] = cost.rolling(30, min_periods=1).mean()
        df["rolling_std_30d"] = cost.rolling(30, min_periods=1).std()

        # ── Percentage change ──
        df["pct_change_1d"] = self._safe_pct_change(cost, df["cost_lag_1d"])
        df["pct_change_7d"] = self._safe_pct_change(cost, df["cost_lag_7d"])
        df["pct_change_30d"] = self._safe_pct_change(cost, df["cost_lag_30d"])

        # ── Z-score ──
        df["z_score_30d"] = np.where(
            df["rolling_std_30d"].isna(),
            np.nan,
            np.where(
                df["rolling_std_30d"] == 0,
                0.0,
                (cost - df["rolling_mean_30d"]) / df["rolling_std_30d"]
            )
        )

        # ── Calendar features ──
        df["feature_date"] = df["agg_date"].dt.date
        df["day_of_week"] = df["agg_date"].dt.dayofweek  # 0=Mon, 6=Sun
        df["day_of_month"] = df["agg_date"].dt.day
        df["week_of_year"] = df["agg_date"].dt.isocalendar().week.astype(int).values
        df["month"] = df["agg_date"].dt.month
        df["is_weekend"] = df["day_of_week"] >= 5
        df["is_month_start"] = df["agg_date"].dt.is_month_start
        df["is_month_end"] = df["agg_date"].dt.is_month_end

        # ── Clean up inf values ──
        df.replace([np.inf, -np.inf], np.nan, inplace=True)

        return df

    def validate_features(self, df: pd.DataFrame) -> List[str]:
        """Validate that all expected feature columns are present."""
        errors: List[str] = []
        for col in self.FEATURE_COLUMNS:
            if col not in df.columns:
                errors.append(f"Missing column: {col}")
        return errors

    @staticmethod
    def _safe_pct_change(current: pd.Series, lag: pd.Series) -> pd.Series:
        """Calculate percentage change, returning NaN when lag is 0 or NaN."""
        result = (current - lag) / lag
        # Replace inf/-inf from division by zero with NaN
        result = result.replace([np.inf, -np.inf], np.nan)
        return result
