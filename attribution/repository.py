import json
import psycopg2.extras
from typing import List, Dict, Optional
from datetime import date

from storage.db import DatabaseManager
from shared.schemas.attribution import AttributionRecord

class AttributionRepository:

    def get_features_for_group(
        self,
        cloud_provider: str,
        service_category: str,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        query = """
        SELECT feature_date AS usage_date,
               account_id, environment, team,
               total_cost_usd, record_count,
               cost_lag_1d, cost_lag_7d, cost_lag_30d,
               rolling_mean_7d, rolling_std_7d,
               rolling_mean_30d, rolling_std_30d,
               pct_change_1d, pct_change_7d, pct_change_30d,
               z_score_30d,
               day_of_week, day_of_month, week_of_year,
               month, is_weekend, is_month_start, is_month_end
        FROM spend_features
        WHERE cloud_provider = %s
          AND service_category = %s
          AND feature_date BETWEEN %s AND %s
        ORDER BY usage_date ASC
        """
        results = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, (cloud_provider, service_category, start_date, end_date))
                for row in cur.fetchall():
                    results.append(dict(row))
        return results

    def get_all_groups(self) -> List[Dict]:
        query = """
        SELECT DISTINCT cloud_provider, service_category
        FROM spend_features
        ORDER BY cloud_provider, service_category
        """
        results = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query)
                for row in cur.fetchall():
                    results.append(dict(row))
        return results

    def upsert_attributions(self, records: List[AttributionRecord]) -> int:
        if not records:
            return 0
            
        query = """
        INSERT INTO cost_attributions (
            attribution_date, cloud_provider, service_category,
            account_id, environment, team, total_cost_usd,
            shap_values, top_driver_1, top_driver_1_value,
            top_driver_2, top_driver_2_value, top_driver_3,
            top_driver_3_value, model_r2_score, feature_count
        ) VALUES %s
        ON CONFLICT (attribution_date, cloud_provider, service_category, account_id, environment, team)
        DO UPDATE SET 
            total_cost_usd = EXCLUDED.total_cost_usd,
            shap_values = EXCLUDED.shap_values,
            top_driver_1 = EXCLUDED.top_driver_1,
            top_driver_1_value = EXCLUDED.top_driver_1_value,
            top_driver_2 = EXCLUDED.top_driver_2,
            top_driver_2_value = EXCLUDED.top_driver_2_value,
            top_driver_3 = EXCLUDED.top_driver_3,
            top_driver_3_value = EXCLUDED.top_driver_3_value,
            model_r2_score = EXCLUDED.model_r2_score,
            feature_count = EXCLUDED.feature_count,
            computed_at = NOW();
        """
        
        values = []
        for r in records:
            values.append((
                r.attribution_date, r.cloud_provider, r.service_category,
                r.account_id, r.environment, r.team, r.total_cost_usd,
                json.dumps(r.shap_values),
                r.top_driver_1, r.top_driver_1_value,
                r.top_driver_2, r.top_driver_2_value,
                r.top_driver_3, r.top_driver_3_value,
                r.model_r2_score, r.feature_count
            ))

        total = 0
        batch_size = 500
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(values), batch_size):
                    batch = values[i:i + batch_size]
                    psycopg2.extras.execute_values(cur, query, batch, page_size=500)
                    total += cur.rowcount
        return total

    def get_attributions(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None,
        service_category: Optional[str] = None,
        top_driver: Optional[str] = None
    ) -> List[AttributionRecord]:
        
        query = "SELECT * FROM cost_attributions WHERE attribution_date BETWEEN %s AND %s"
        params = [start_date, end_date]

        if cloud_provider:
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)
            
        if service_category:
            query += " AND service_category = %s"
            params.append(service_category)
            
        if top_driver:
            query += " AND (top_driver_1 = %s OR top_driver_2 = %s OR top_driver_3 = %s)"
            params.extend([top_driver, top_driver, top_driver])

        query += " ORDER BY attribution_date DESC"

        results = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    shap_vals = row.get("shap_values")
                    if isinstance(shap_vals, str):
                        shap_vals = json.loads(shap_vals)
                        
                    results.append(AttributionRecord(
                        attribution_date=row["attribution_date"],
                        cloud_provider=row["cloud_provider"],
                        service_category=row["service_category"],
                        account_id=row["account_id"],
                        environment=row["environment"],
                        team=row["team"],
                        total_cost_usd=row["total_cost_usd"],
                        shap_values=shap_vals,
                        top_driver_1=row["top_driver_1"],
                        top_driver_1_value=row["top_driver_1_value"],
                        top_driver_2=row["top_driver_2"],
                        top_driver_2_value=row["top_driver_2_value"],
                        top_driver_3=row["top_driver_3"],
                        top_driver_3_value=row["top_driver_3_value"],
                        model_r2_score=row["model_r2_score"],
                        feature_count=row["feature_count"],
                        computed_at=row["computed_at"]
                    ))
        return results
