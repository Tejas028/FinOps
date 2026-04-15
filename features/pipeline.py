import time
import logging
import pandas as pd
from datetime import date, timedelta
from typing import Optional, List
from pydantic import BaseModel

from features.repository import FeatureRepository
from features.calculator import FeatureCalculator

logger = logging.getLogger(__name__)


class FeaturePipelineResult(BaseModel):
    start_date: date
    end_date: date
    groups_processed: int
    features_written: int
    duration_seconds: float
    errors: List[str] = []


class FeatureEngineeringPipeline:

    def __init__(self):
        self.repository = FeatureRepository()
        self.calculator = FeatureCalculator()

    def run(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None
    ) -> FeaturePipelineResult:
        """
        Orchestrate: DB read -> group -> compute -> DB write.
        """
        t0 = time.time()
        errors: List[str] = []

        # 1. Fetch daily_aggregates (with 30-day warmup window)
        raw_rows = self.repository.get_daily_aggregates_for_features(
            start_date=start_date,
            end_date=end_date,
            cloud_provider=cloud_provider
        )

        if not raw_rows:
            return FeaturePipelineResult(
                start_date=start_date,
                end_date=end_date,
                groups_processed=0,
                features_written=0,
                duration_seconds=time.time() - t0,
                errors=["No daily_aggregates data found for the given range."]
            )

        # 2. Load into pandas DataFrame
        df = pd.DataFrame(raw_rows)

        # 3. Group by the 5-column composite key
        group_keys = ["cloud_provider", "service_category", "account_id",
                       "environment", "team"]
        grouped = df.groupby(group_keys, sort=False)

        groups_processed = 0
        all_features: List[dict] = []

        # 4. Process each group
        for group_name, group_df in grouped:
            try:
                group_df = group_df.sort_values("agg_date").reset_index(drop=True)

                # Compute features
                featured_df = self.calculator.compute_features(group_df)

                # Validate
                validation_errors = self.calculator.validate_features(featured_df)
                if validation_errors:
                    errors.extend([
                        f"Group {group_name}: {e}" for e in validation_errors
                    ])
                    continue

                # Filter to target date range (discard warmup rows)
                featured_df["agg_date_dt"] = pd.to_datetime(featured_df["agg_date"])
                mask = featured_df["agg_date_dt"].dt.date >= start_date
                target_df = featured_df[mask].copy()

                if target_df.empty:
                    continue

                # Convert to list of dicts for upsert
                records = target_df.to_dict(orient="records")
                all_features.extend(records)
                groups_processed += 1

            except Exception as e:
                errors.append(f"Group {group_name}: {str(e)}")
                logger.error(f"Error processing group {group_name}: {e}")

        # 5. Batch upsert
        features_written = 0
        if all_features:
            features_written = self.repository.upsert_features(all_features)

        duration = time.time() - t0

        return FeaturePipelineResult(
            start_date=start_date,
            end_date=end_date,
            groups_processed=groups_processed,
            features_written=features_written,
            duration_seconds=duration,
            errors=errors
        )

    def run_incremental(
        self,
        days_back: int = 7
    ) -> FeaturePipelineResult:
        """Recompute features for the last N days."""
        today = date.today()
        return self.run(
            start_date=today - timedelta(days=days_back),
            end_date=today
        )
