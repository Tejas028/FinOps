import psycopg2.extras
from storage.db import DatabaseManager
from datetime import date, timedelta
from typing import List, Dict, Any, Optional


class FeatureRepository:
    """All DB reads/writes for the features module."""

    def get_daily_aggregates_for_features(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Read from daily_aggregates for the feature computation window.
        Fetches from (start_date - 30 days) to end_date for rolling warmup.
        """
        warmup_start = start_date - timedelta(days=30)

        query = """
        SELECT agg_date, cloud_provider, service_category,
               account_id, environment, team,
               total_cost_usd, record_count
        FROM daily_aggregates
        WHERE agg_date BETWEEN %s AND %s
        """
        params: list = [warmup_start, end_date]

        if cloud_provider:
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)

        query += """
        ORDER BY cloud_provider, service_category,
                 account_id, environment, team, agg_date ASC
        """

        results: List[Dict[str, Any]] = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                cols = [desc[0] for desc in cur.description]
                for row in cur.fetchall():
                    results.append(dict(zip(cols, row)))
        return results

    def upsert_features(
        self,
        features: List[Dict[str, Any]]
    ) -> int:
        """
        Bulk upsert into spend_features.
        Uses INSERT ... ON CONFLICT DO UPDATE in batches of 1,000.
        """
        if not features:
            return 0

        query = """
        INSERT INTO spend_features (
            feature_date, cloud_provider, service_category, account_id,
            environment, team, total_cost_usd, record_count,
            cost_lag_1d, cost_lag_7d, cost_lag_30d,
            rolling_mean_7d, rolling_std_7d, rolling_mean_30d, rolling_std_30d,
            pct_change_1d, pct_change_7d, pct_change_30d,
            z_score_30d,
            day_of_week, day_of_month, week_of_year, month,
            is_weekend, is_month_start, is_month_end
        ) VALUES %s
        ON CONFLICT (feature_date, cloud_provider, service_category,
                     account_id, environment, team)
        DO UPDATE SET
            total_cost_usd   = EXCLUDED.total_cost_usd,
            record_count     = EXCLUDED.record_count,
            cost_lag_1d      = EXCLUDED.cost_lag_1d,
            cost_lag_7d      = EXCLUDED.cost_lag_7d,
            cost_lag_30d     = EXCLUDED.cost_lag_30d,
            rolling_mean_7d  = EXCLUDED.rolling_mean_7d,
            rolling_std_7d   = EXCLUDED.rolling_std_7d,
            rolling_mean_30d = EXCLUDED.rolling_mean_30d,
            rolling_std_30d  = EXCLUDED.rolling_std_30d,
            pct_change_1d    = EXCLUDED.pct_change_1d,
            pct_change_7d    = EXCLUDED.pct_change_7d,
            pct_change_30d   = EXCLUDED.pct_change_30d,
            z_score_30d      = EXCLUDED.z_score_30d,
            day_of_week      = EXCLUDED.day_of_week,
            day_of_month     = EXCLUDED.day_of_month,
            week_of_year     = EXCLUDED.week_of_year,
            month            = EXCLUDED.month,
            is_weekend       = EXCLUDED.is_weekend,
            is_month_start   = EXCLUDED.is_month_start,
            is_month_end     = EXCLUDED.is_month_end,
            computed_at      = NOW();
        """

        total_upserted = 0
        batch_size = 1000

        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(features), batch_size):
                    batch = features[i:i + batch_size]
                    values = []
                    for f in batch:
                        values.append((
                            f["feature_date"],
                            f["cloud_provider"],
                            f["service_category"],
                            f["account_id"],
                            f.get("environment", "unknown"),
                            f.get("team", "unknown"),
                            f["total_cost_usd"],
                            f["record_count"],
                            self._nan_to_none(f.get("cost_lag_1d")),
                            self._nan_to_none(f.get("cost_lag_7d")),
                            self._nan_to_none(f.get("cost_lag_30d")),
                            self._nan_to_none(f.get("rolling_mean_7d")),
                            self._nan_to_none(f.get("rolling_std_7d")),
                            self._nan_to_none(f.get("rolling_mean_30d")),
                            self._nan_to_none(f.get("rolling_std_30d")),
                            self._nan_to_none(f.get("pct_change_1d")),
                            self._nan_to_none(f.get("pct_change_7d")),
                            self._nan_to_none(f.get("pct_change_30d")),
                            self._nan_to_none(f.get("z_score_30d")),
                            f.get("day_of_week"),
                            f.get("day_of_month"),
                            f.get("week_of_year"),
                            f.get("month"),
                            f.get("is_weekend"),
                            f.get("is_month_start"),
                            f.get("is_month_end"),
                        ))
                    psycopg2.extras.execute_values(cur, query, values, page_size=1000)
                    total_upserted += cur.rowcount

        return total_upserted

    def get_features(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None,
        service_category: Optional[str] = None,
        account_id: Optional[str] = None,
        min_z_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Read features for downstream modules."""
        query = """
        SELECT feature_date, cloud_provider, service_category, account_id,
               environment, team, total_cost_usd, record_count,
               cost_lag_1d, cost_lag_7d, cost_lag_30d,
               rolling_mean_7d, rolling_std_7d, rolling_mean_30d, rolling_std_30d,
               pct_change_1d, pct_change_7d, pct_change_30d,
               z_score_30d,
               day_of_week, day_of_month, week_of_year, month,
               is_weekend, is_month_start, is_month_end, computed_at
        FROM spend_features
        WHERE feature_date BETWEEN %s AND %s
        """
        params: list = [start_date, end_date]

        if cloud_provider:
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)
        if service_category:
            query += " AND service_category = %s"
            params.append(service_category)
        if account_id:
            query += " AND account_id = %s"
            params.append(account_id)
        if min_z_score is not None:
            query += " AND ABS(z_score_30d) >= %s"
            params.append(min_z_score)

        query += " ORDER BY feature_date ASC, cloud_provider, service_category"

        results: List[Dict[str, Any]] = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                cols = [desc[0] for desc in cur.description]
                for row in cur.fetchall():
                    results.append(dict(zip(cols, row)))
        return results

    def get_feature_series(
        self,
        cloud_provider: str,
        service_category: str,
        account_id: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Return the full time-series of features for ONE specific
        (cloud x service x account) combination, ordered by date.
        """
        query = """
        SELECT feature_date, cloud_provider, service_category, account_id,
               environment, team, total_cost_usd, record_count,
               cost_lag_1d, cost_lag_7d, cost_lag_30d,
               rolling_mean_7d, rolling_std_7d, rolling_mean_30d, rolling_std_30d,
               pct_change_1d, pct_change_7d, pct_change_30d,
               z_score_30d,
               day_of_week, day_of_month, week_of_year, month,
               is_weekend, is_month_start, is_month_end, computed_at
        FROM spend_features
        WHERE cloud_provider = %s
          AND service_category = %s
          AND account_id = %s
          AND feature_date BETWEEN %s AND %s
        ORDER BY feature_date ASC
        """

        results: List[Dict[str, Any]] = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (cloud_provider, service_category,
                                    account_id, start_date, end_date))
                cols = [desc[0] for desc in cur.description]
                for row in cur.fetchall():
                    results.append(dict(zip(cols, row)))
        return results

    @staticmethod
    def _nan_to_none(value):
        """Convert NaN/inf floats to None for PostgreSQL compatibility."""
        import math
        if value is None:
            return None
        try:
            if math.isnan(value) or math.isinf(value):
                return None
        except (TypeError, ValueError):
            pass
        return value
