import time
import logging
import pandas as pd
from datetime import date
from typing import List, Optional

from detection.detectors.zscore_detector import ZScoreDetector
from detection.detectors.isolation_forest_detector import IsolationForestDetector
from detection.detectors.lstm_detector import LSTMDetector
from detection.ensemble.scorer import EnsembleScorer
from detection import config
from features.repository import FeatureRepository
from shared.schemas.anomaly import AnomalyResult

logger = logging.getLogger(__name__)


class DetectionEngine:
    """Main anomaly detection orchestrator."""

    def __init__(self, mode: str = "train_predict"):
        self.mode = mode
        self.zscore = ZScoreDetector()
        self.iforest = IsolationForestDetector()
        self.lstm = LSTMDetector()
        self.ensemble = EnsembleScorer()
        self.feature_repo = FeatureRepository()
        from storage.client import StorageClient
        self.storage_client = StorageClient()

    def run(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None,
        force_retrain: bool = False,
    ) -> List[AnomalyResult]:
        t0 = time.time()

        # Step 1: Load features from spend_features
        features = self.feature_repo.get_features(
            start_date=start_date,
            end_date=end_date,
            cloud_provider=cloud_provider,
        )
        if len(features) < 30:
            raise ValueError(f"Only {len(features)} feature rows found. Need >= 30.")

        df = pd.DataFrame(features)
        print(f"Loaded {len(df)} feature rows for detection.")

        # Step 2: Fit if mode includes "train"
        if "train" in self.mode:
            if not force_retrain:
                try:
                    self.iforest.load(config.MODEL_REGISTRY_PATH)
                    self.lstm.load(config.MODEL_REGISTRY_PATH)
                except Exception:
                    pass

            if force_retrain or not self.iforest.models:
                print("Training IsolationForest models...")
                self.iforest.fit(df)
                self.iforest.save(config.MODEL_REGISTRY_PATH)

            if config.ENSEMBLE_WEIGHT_LSTM > 0:
                if force_retrain or not self.lstm.models:
                    print("Training LSTM models...")
                    self.lstm.fit(df)
                    self.lstm.save(config.MODEL_REGISTRY_PATH)

        # Step 3: If predict-only, load saved models
        if self.mode == "predict":
            self.iforest.load(config.MODEL_REGISTRY_PATH)
            if config.ENSEMBLE_WEIGHT_LSTM > 0:
                self.lstm.load(config.MODEL_REGISTRY_PATH)

        # Step 4: Run all detectors
        print("Running Z-Score detector...")
        zscore_results = self.zscore.predict(df)
        print("Running IsolationForest detector...")
        iforest_results = self.iforest.predict(df)
        
        lstm_results = []
        if config.ENSEMBLE_WEIGHT_LSTM > 0:
            print("Running LSTM detector...")
            lstm_results = self.lstm.predict(df)
        else:
            print("Skipping LSTM detector (weight = 0).")
            # If skipping, we need a list of None to keep indices aligned for the map
            lstm_results = [None] * len(df)

        # Build lookup maps by index
        zscore_map = {i: r for i, r in enumerate(zscore_results)}
        iforest_map = {i: r for i, r in enumerate(iforest_results)}
        lstm_map = {i: r for i, r in enumerate(lstm_results)}

        # Step 5: Ensemble scoring
        anomaly_results: List[AnomalyResult] = []
        all_metadata: List[dict] = []

        for idx, row_dict in enumerate(features):
            zr = zscore_map.get(idx)
            ir = iforest_map.get(idx)
            lr = lstm_map.get(idx)

            result = self.ensemble.score_to_anomaly_result(row_dict, zr, ir, lr)
            if result is not None:
                ensemble_score = self.ensemble.score(zr, ir, lr)
                meta = self.ensemble.build_metadata(row_dict, zr, ir, lr, ensemble_score)
                anomaly_results.append(result)
                all_metadata.append(meta)

        # Step 6: Write to DB
        written = 0
        flags_updated = 0
        try:
            from storage.db import DatabaseManager
            DatabaseManager.initialize()
            written = self.storage_client.write_anomalies(anomaly_results, all_metadata)
            
            severity_groups = {}
            for ar, meta in zip(anomaly_results, all_metadata):
                sev = ar.severity.value if hasattr(ar.severity, 'value') else ar.severity
                severity_groups.setdefault(sev, []).append(meta)
            
            for severity, dimension_list in severity_groups.items():
                flags_updated += self.storage_client.update_anomaly_flags(dimension_list, True, severity, use_dimensions=True)
        except Exception as e:
            logger.error(f"DB write failed: {e}")
            print(f"Warning: DB write failed: {e}")

        duration = time.time() - t0

        # Step 7: Print summary
        self._print_summary(df, anomaly_results, all_metadata, duration, written, flags_updated)

        return anomaly_results

    def _print_summary(self, df, anomaly_results, all_metadata, duration, written, flags_updated):
        from rich.console import Console
        from rich.table import Table

        stats = {}
        for _, row in df.iterrows():
            key = (row.get("cloud_provider", "unknown"), row.get("service_category", "unknown"))
            if key not in stats:
                stats[key] = {"total_rows": 0, "anomalies": 0, "critical": 0, "high": 0}
            stats[key]["total_rows"] += 1
            
        for meta, ar in zip(all_metadata, anomaly_results):
            key = (meta["cloud_provider"], meta["service"])
            if key not in stats:
                stats[key] = {"total_rows": 0, "anomalies": 0, "critical": 0, "high": 0}
            stats[key]["anomalies"] += 1
            sev = getattr(ar.severity, "value", str(ar.severity))
            if sev == "critical":
                stats[key]["critical"] += 1
            elif sev == "high":
                stats[key]["high"] += 1
                
        console = Console()
        table = Table(title="Anomaly Detection Summary")
        table.add_column("Cloud", style="cyan")
        table.add_column("Service", style="magenta")
        table.add_column("Total Rows", justify="right")
        table.add_column("Anomalies", justify="right")
        table.add_column("Rate", justify="right")
        table.add_column("Critical", style="red", justify="right")
        table.add_column("High", style="yellow", justify="right")
        
        for (cloud, service), data in sorted(stats.items()):
            rate = f"{(data['anomalies'] / data['total_rows'] * 100):.1f}%" if data['total_rows'] > 0 else "0.0%"
            table.add_row(
                str(cloud), str(service), str(data["total_rows"]),
                str(data["anomalies"]), rate,
                str(data["critical"]), str(data["high"])
            )
            
        print(f"\n{'='*60}")
        console.print(table)
        print(f"Total feature rows analyzed:  {len(df)}")
        print(f"Total anomalies detected:     {len(anomaly_results)}")
        print(f"Written to DB:                {written}")
        print(f"Flags updated:                {flags_updated}")
        print(f"Duration:                     {duration:.1f}s")
        print(f"{'='*60}")
