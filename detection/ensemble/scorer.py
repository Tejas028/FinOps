import uuid
from datetime import datetime, timezone
from typing import Optional, List

from detection.detectors.base_detector import DetectorResult
from detection import config
from shared.schemas.anomaly import AnomalyResult
from shared.schemas.billing import AnomalySeverity


class EnsembleScorer:
    """Combines detector scores via weighted average with graceful degradation."""

    def score(
        self,
        zscore_result: Optional[DetectorResult],
        iforest_result: Optional[DetectorResult],
        lstm_result: Optional[DetectorResult],
    ) -> float:
        """Compute weighted ensemble score with graceful degradation."""
        scores = {}
        weights = {}

        if zscore_result is not None:
            scores["zscore"] = zscore_result.raw_score
            weights["zscore"] = config.ENSEMBLE_WEIGHT_ZSCORE
        if iforest_result is not None:
            scores["iforest"] = iforest_result.raw_score
            weights["iforest"] = config.ENSEMBLE_WEIGHT_IFOREST
        if lstm_result is not None:
            scores["lstm"] = lstm_result.raw_score
            weights["lstm"] = config.ENSEMBLE_WEIGHT_LSTM

        if not weights:
            return 0.0

        # Redistribute weights proportionally
        total_weight = sum(weights.values())
        ensemble = sum(
            scores[k] * (weights[k] / total_weight) for k in scores
        )
        return float(ensemble)

    def map_severity(self, score: float) -> Optional[str]:
        """Map ensemble score to severity string. Returns None if below threshold."""
        if score >= config.SEVERITY_THRESHOLDS["critical"]:
            return "critical"
        elif score >= config.SEVERITY_THRESHOLDS["high"]:
            return "high"
        elif score >= config.SEVERITY_THRESHOLDS["medium"]:
            return "medium"
        elif score >= config.SEVERITY_THRESHOLDS["low"]:
            return "low"
        return None

    def score_to_anomaly_result(
        self,
        row: dict,
        zscore_result: Optional[DetectorResult],
        iforest_result: Optional[DetectorResult],
        lstm_result: Optional[DetectorResult],
    ) -> Optional[AnomalyResult]:
        """Produce AnomalyResult if ensemble_score >= 0.30, else None."""
        ensemble_score = self.score(zscore_result, iforest_result, lstm_result)
        severity = self.map_severity(ensemble_score)

        if severity is None:
            return None

        # Pick best available expected cost
        expected_costs = []
        actual_cost = float(row.get("total_cost_usd", 0) or 0)
        for r in [zscore_result, iforest_result, lstm_result]:
            if r is not None and r.expected_cost > 0:
                expected_costs.append(r.expected_cost)
        expected_cost = sum(expected_costs) / len(expected_costs) if expected_costs else 0.0

        deviation_pct = ((actual_cost - expected_cost) / expected_cost * 100) if expected_cost > 0 else 0.0

        z_score_val = zscore_result.z_score if zscore_result else None

        return AnomalyResult(
            anomaly_id=str(uuid.uuid4()),
            record_id=str(row.get("record_id", f"{row.get('cloud_provider')}_{row.get('service_category')}_{row.get('account_id')}_{row.get('feature_date')}")),
            detection_method="ensemble",
            severity=AnomalySeverity(severity),
            z_score=z_score_val,
            expected_cost=expected_cost,
            actual_cost=actual_cost,
            deviation_pct=deviation_pct,
            detected_at=datetime.now(timezone.utc),
            shap_attribution=None,
        )

    def build_metadata(
        self,
        row: dict,
        zscore_result: Optional[DetectorResult],
        iforest_result: Optional[DetectorResult],
        lstm_result: Optional[DetectorResult],
        ensemble_score: float,
    ) -> dict:
        """Build metadata dict for DB storage."""
        return {
            "cloud_provider": str(row.get("cloud_provider", "")),
            "service": str(row.get("service_category", "")),
            "account_id": str(row.get("account_id", "")),
            "usage_date": row.get("feature_date", row.get("agg_date")),
            "zscore_score": zscore_result.raw_score if zscore_result else None,
            "iforest_score": iforest_result.raw_score if iforest_result else None,
            "lstm_score": lstm_result.raw_score if lstm_result else None,
            "ensemble_score": ensemble_score,
        }
