import pandas as pd
import numpy as np
from typing import List
from detection.detectors.base_detector import BaseDetector, DetectorResult


class ZScoreDetector(BaseDetector):
    """Statistical detector using z_score_30d from spend_features."""

    def fit(self, df: pd.DataFrame) -> None:
        """No-op — purely statistical, no training needed."""
        pass

    def predict(self, df: pd.DataFrame) -> List[DetectorResult]:
        results = []
        for _, row in df.iterrows():
            z = row.get("z_score_30d")
            if z is None or (isinstance(z, float) and np.isnan(z)):
                z_val = 0.0
            else:
                z_val = float(z)

            # Score mapping: score = min(1.0, max(0.0, (|z| - 1.5) / 3.5))
            raw_score = min(1.0, max(0.0, (abs(z_val) - 1.5) / 3.5))

            expected = float(row.get("rolling_mean_30d", 0) or 0)
            actual = float(row.get("total_cost_usd", 0) or 0)
            if expected > 0:
                deviation_pct = ((actual - expected) / expected) * 100
            else:
                deviation_pct = 0.0

            results.append(DetectorResult(
                record_id=str(row.get("record_id", f"{row.get('cloud_provider')}_{row.get('service_category')}_{row.get('account_id')}_{row.get('feature_date')}")),
                usage_date=row.get("feature_date", row.get("agg_date")),
                cloud_provider=str(row.get("cloud_provider", "")),
                service=str(row.get("service_category", "")),
                account_id=str(row.get("account_id", "")),
                raw_score=raw_score,
                z_score=z_val,
                expected_cost=expected,
                actual_cost=actual,
                deviation_pct=deviation_pct,
                detector_name="zscore"
            ))
        return results

    def save(self, path: str) -> None:
        pass  # No state to save

    def load(self, path: str) -> None:
        pass  # No state to load
