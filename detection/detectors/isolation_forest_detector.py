import os
import logging
import numpy as np
import pandas as pd
import joblib
from typing import List, Dict, Optional
from sklearn.ensemble import IsolationForest

from detection.detectors.base_detector import BaseDetector, DetectorResult
from detection import config

logger = logging.getLogger(__name__)


class IsolationForestDetector(BaseDetector):
    """Per-(cloud, service) IsolationForest detector."""

    def __init__(self):
        self.models: Dict[str, IsolationForest] = {}
        self.score_ranges: Dict[str, tuple] = {}  # (min, max) of decision_function on train

    def fit(self, df: pd.DataFrame) -> None:
        groups = df.groupby(["cloud_provider", "service_category"])
        for (cloud, service), group_df in groups:
            key = f"{cloud}_{service}"
            if len(group_df) < config.MIN_ROWS_FOR_IFOREST:
                logger.info(f"Skipping IForest for {key}: only {len(group_df)} rows")
                continue

            features = self._extract_features(group_df)
            if features is None or len(features) == 0:
                continue

            model = IsolationForest(
                n_estimators=config.IFOREST_N_ESTIMATORS,
                contamination=config.IFOREST_CONTAMINATION,
                max_samples=config.IFOREST_MAX_SAMPLES,
                random_state=config.IFOREST_RANDOM_STATE,
            )
            model.fit(features)

            # Cache score range for normalization
            scores = model.decision_function(features)
            self.score_ranges[key] = (float(np.min(scores)), float(np.max(scores)))
            self.models[key] = model

    def predict(self, df: pd.DataFrame) -> List[DetectorResult]:
        results = []
        for _, row in df.iterrows():
            cloud = str(row.get("cloud_provider", ""))
            service = str(row.get("service_category", ""))
            key = f"{cloud}_{service}"

            expected = float(row.get("rolling_mean_30d", 0) or 0)
            actual = float(row.get("total_cost_usd", 0) or 0)
            deviation_pct = ((actual - expected) / expected * 100) if expected > 0 else 0.0

            if key not in self.models:
                results.append(DetectorResult(
                    record_id=str(row.get("record_id", f"{cloud}_{service}_{row.get('account_id')}_{row.get('feature_date')}")),
                    usage_date=row.get("feature_date", row.get("agg_date")),
                    cloud_provider=cloud, service=service,
                    account_id=str(row.get("account_id", "")),
                    raw_score=0.0, expected_cost=expected,
                    actual_cost=actual, deviation_pct=deviation_pct,
                    detector_name="isolation_forest"
                ))
                continue

            feature_row = self._extract_single_row(row)
            if feature_row is None:
                raw_score = 0.0
            else:
                model = self.models[key]
                score = model.decision_function(feature_row.reshape(1, -1))[0]
                smin, smax = self.score_ranges.get(key, (-1, 1))
                rng = smax - smin if smax != smin else 1.0
                raw_score = float(np.clip(1.0 - (score - smin) / rng, 0.0, 1.0))

            results.append(DetectorResult(
                record_id=str(row.get("record_id", f"{cloud}_{service}_{row.get('account_id')}_{row.get('feature_date')}")),
                usage_date=row.get("feature_date", row.get("agg_date")),
                cloud_provider=cloud, service=service,
                account_id=str(row.get("account_id", "")),
                raw_score=raw_score, expected_cost=expected,
                actual_cost=actual, deviation_pct=deviation_pct,
                detector_name="isolation_forest"
            ))
        return results

    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        for key, model in self.models.items():
            joblib.dump(model, os.path.join(path, f"iforest_{key}.pkl"))
            joblib.dump(self.score_ranges.get(key), os.path.join(path, f"iforest_{key}_range.pkl"))

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            return
        for fname in os.listdir(path):
            if fname.startswith("iforest_") and fname.endswith(".pkl") and "_range" not in fname:
                key = fname.replace("iforest_", "").replace(".pkl", "")
                self.models[key] = joblib.load(os.path.join(path, fname))
                range_file = os.path.join(path, f"iforest_{key}_range.pkl")
                if os.path.exists(range_file):
                    self.score_ranges[key] = joblib.load(range_file)

    def _extract_features(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        cols = [c for c in config.IFOREST_FEATURE_COLS if c in df.columns]
        if not cols:
            return None
        subset = df[cols].copy()
        # Convert booleans to int
        for c in subset.columns:
            if subset[c].dtype == bool:
                subset[c] = subset[c].astype(int)
        subset = subset.fillna(0)
        return subset.values

    def _extract_single_row(self, row) -> Optional[np.ndarray]:
        vals = []
        for c in config.IFOREST_FEATURE_COLS:
            v = row.get(c, 0)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                v = 0.0
            if isinstance(v, bool):
                v = int(v)
            vals.append(float(v))
        return np.array(vals)
