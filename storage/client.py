import time
import json
import psycopg2.extras
from typing import List, Optional, Dict, Any
from datetime import date

from shared.schemas.normalized import NormalizedRecord
from shared.schemas.anomaly import AnomalyResult
from shared.schemas.forecast import ForecastResult
from storage.db import DatabaseManager
from storage.models import UpsertResult

class StorageClient:

    # ── Write Operations ──────────────────────────────────────

    def upsert_records(
        self,
        records: List[NormalizedRecord]
    ) -> UpsertResult:
        """
        Bulk insert NormalizedRecords using PostgreSQL's
        INSERT ... ON CONFLICT (fingerprint) DO NOTHING.
        """
        start_time = time.time()
        inserted_total = 0
        skipped_total = 0

        query = """
        INSERT INTO billing_records (
            record_id, fingerprint, cloud_provider, account_id,
            service_name_raw, service_category, region, resource_id,
            usage_date, cost_original, currency_original, cost_usd,
            usage_quantity, usage_unit, tags_raw, tags, environment, team
        ) VALUES %s
        ON CONFLICT (usage_date, fingerprint) DO NOTHING;
        """

        # Batch in groups of 1000
        batch_size = 1000
        
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    values = [
                        (
                            r.record_id,
                            r.fingerprint,
                            r.cloud_provider,
                            r.account_id,
                            r.service_name_raw,
                            r.service_category,
                            r.region,
                            r.resource_id,
                            r.usage_date,
                            r.cost_original,
                            r.currency_original,
                            r.cost_usd,
                            r.usage_quantity,
                            r.usage_unit,
                            r.tags_raw,
                            json.dumps(r.tags) if r.tags is not None else None,
                            r.environment,
                            r.team
                        )
                        for r in batch
                    ]
                    
                    try:
                        psycopg2.extras.execute_values(cur, query, values, page_size=1000)
                        inserted = cur.rowcount
                        inserted_total += inserted
                        skipped_total += (len(batch) - inserted)
                    except Exception as e:
                        print(f"Error executing batch insert: {e}")
                        raise

        duration = time.time() - start_time
        return UpsertResult(
            inserted=inserted_total,
            skipped=skipped_total,
            total=len(records),
            duration_seconds=duration
        )

    def log_ingestion_run(
        self,
        cloud_provider: str,
        inserted: int,
        skipped: int,
        date_start: date,
        date_end: date,
        duration_seconds: float,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Write a row to ingestion_log table."""
        query = """
        INSERT INTO ingestion_log (
            cloud_provider, records_inserted, records_skipped,
            date_range_start, date_range_end, duration_seconds, status, error_message
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            with DatabaseManager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (
                        cloud_provider, inserted, skipped,
                        date_start, date_end, duration_seconds,
                        status, error_message
                    ))
        except Exception as e:
            # We don't want a logging failure to crash pipelines
            print(f"Warning: Failed to log ingestion run: {e}")

    # ── Read Operations ───────────────────────────────────────

    def get_records(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None,
        service_category: Optional[str] = None,
        account_id: Optional[str] = None,
        environment: Optional[str] = None,
        team: Optional[str] = None,
        limit: int = 10_000
    ) -> List[NormalizedRecord]:
        
        query = """
        SELECT
            record_id, fingerprint, cloud_provider, account_id,
            service_name_raw, service_category, region, resource_id,
            usage_date, ingested_at, cost_original, currency_original, cost_usd,
            usage_quantity, usage_unit, tags_raw, tags, environment, team,
            anomaly_flag, anomaly_severity
        FROM billing_records
        WHERE usage_date BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if cloud_provider:
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)
        if service_category:
            query += " AND service_category = %s"
            params.append(service_category)
        if account_id:
            query += " AND account_id = %s"
            params.append(account_id)
        if environment:
            query += " AND environment = %s"
            params.append(environment)
        if team:
            query += " AND team = %s"
            params.append(team)

        query += " ORDER BY usage_date DESC LIMIT %s"
        params.append(limit)

        records = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                for r in rows:
                    records.append(NormalizedRecord(
                        record_id=r[0],
                        fingerprint=r[1],
                        cloud_provider=r[2],
                        account_id=r[3],
                        service_name_raw=r[4],
                        service_category=r[5],
                        region=r[6],
                        resource_id=r[7],
                        usage_date=r[8],
                        ingested_at=r[9],
                        cost_original=r[10],
                        currency_original=r[11],
                        cost_usd=r[12],
                        usage_quantity=r[13],
                        usage_unit=r[14],
                        tags_raw=r[15] or "",
                        tags=r[16] if r[16] is not None else {},
                        environment=r[17],
                        team=r[18],
                        anomaly_flag=r[19],
                        anomaly_severity=r[20]
                    ))
        return records

    def get_daily_aggregates(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None,
        service_category: Optional[str] = None,
        group_by: List[str] = ["agg_date", "cloud_provider"]
    ) -> List[Dict[str, Any]]:
        
        valid_cols = {"agg_date", "cloud_provider", "service_category", "account_id", "environment", "team"}
        group_fields = [f for f in group_by if f in valid_cols]
        if not group_fields:
            group_fields = ["agg_date", "cloud_provider"]
            
        select_clause = ", ".join(group_fields)
        
        query = f"""
        SELECT {select_clause}, SUM(total_cost_usd) as total_cost, SUM(record_count) as total_records
        FROM daily_aggregates
        WHERE agg_date BETWEEN %s AND %s
        """
        params = [start_date, end_date]

        if cloud_provider:
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)
        if service_category:
            query += " AND service_category = %s"
            params.append(service_category)

        query += f" GROUP BY {select_clause} ORDER BY {group_fields[0]} DESC"

        results = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                cols = [desc[0] for desc in cur.description]
                for row in cur.fetchall():
                    results.append(dict(zip(cols, row)))
        return results

    def get_spend_summary(
        self,
        start_date: date,
        end_date: date,
        group_by: str = "cloud_provider"
    ) -> List[Dict[str, Any]]:
        valid_groups = {"cloud_provider", "service_category", "environment", "team", "account_id"}
        if group_by not in valid_groups:
            group_by = "cloud_provider"

        query = f"""
        SELECT {group_by}, SUM(cost_usd) as total_cost, COUNT(*) as record_count
        FROM billing_records
        WHERE usage_date BETWEEN %s AND %s
        GROUP BY {group_by}
        ORDER BY total_cost DESC
        """
        
        results = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (start_date, end_date))
                for row in cur.fetchall():
                    results.append({
                        group_by: row[0],
                        "total_cost": row[1],
                        "record_count": row[2]
                    })
        return results

    def get_record_count(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        
        query = "SELECT COUNT(*) FROM billing_records"
        params = []
        if start_date and end_date:
            query += " WHERE usage_date BETWEEN %s AND %s"
            params.append(start_date)
            params.append(end_date)
            
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                return cur.fetchone()[0]

    # ── Aggregate Refresh ─────────────────────────────────────

    def refresh_daily_aggregates(
        self,
        start_date: date,
        end_date: date
    ) -> int:
        
        query = """
        INSERT INTO daily_aggregates
            (agg_date, cloud_provider, service_category, account_id,
             environment, team, total_cost_usd, record_count, avg_cost_usd)
        SELECT
            usage_date AS agg_date,
            cloud_provider,
            service_category,
            account_id,
            COALESCE(environment, 'unknown'),
            COALESCE(team, 'unknown'),
            SUM(cost_usd),
            COUNT(*),
            AVG(cost_usd)
        FROM billing_records
        WHERE usage_date BETWEEN %s AND %s
        GROUP BY usage_date, cloud_provider, service_category,
                 account_id, environment, team
        ON CONFLICT (agg_date, cloud_provider, service_category, account_id, environment, team)
        DO UPDATE SET
            total_cost_usd = EXCLUDED.total_cost_usd,
            record_count   = EXCLUDED.record_count,
            avg_cost_usd   = EXCLUDED.avg_cost_usd;
        """
        
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (start_date, end_date))
                return cur.rowcount

    # ── Anomaly Update ─────────────────────────────────────────

    def update_anomaly_flags(
        self,
        identifiers: List[Any],
        anomaly_flag: bool,
        anomaly_severity: Optional[str],
        use_dimensions: bool = False
    ) -> int:
        
        if not identifiers:
            return 0
            
        if use_dimensions:
            # identifiers is a list of dicts with: cloud_provider, service_category, account_id, usage_date
            query = """
            UPDATE billing_records
            SET anomaly_flag = %s, anomaly_severity = %s
            WHERE (cloud_provider, service_category, account_id, usage_date) IN %s
            """
            dims = [
                (d["cloud_provider"], d["service"], d["account_id"], d["usage_date"])
                for d in identifiers
            ]
            with DatabaseManager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (anomaly_flag, anomaly_severity, tuple(dims)))
                    return cur.rowcount
        else:
            # legacy fingerprint/record_id lookup
            query = """
            UPDATE billing_records
            SET anomaly_flag = %s, anomaly_severity = %s
            WHERE fingerprint IN %s OR record_id IN %s
            """
            with DatabaseManager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (anomaly_flag, anomaly_severity, tuple(identifiers), tuple(identifiers)))
                    return cur.rowcount

    def write_anomalies(self, anomalies: List[AnomalyResult], metadata: List[dict]) -> int:
        """
        Bulk upsert anomaly rows. metadata is a list of dicts with:
        cloud_provider, service, account_id, usage_date,
        zscore_score, iforest_score, lstm_score, ensemble_score.
        Returns count of rows written.
        """
        if not anomalies:
            return 0

        query = """
        INSERT INTO anomalies (
            anomaly_id, record_id, detection_method, severity,
            z_score, expected_cost, actual_cost, deviation_pct,
            detected_at, shap_attribution,
            cloud_provider, service, account_id, usage_date,
            zscore_score, iforest_score, lstm_score, ensemble_score
        ) VALUES %s
        ON CONFLICT (anomaly_id) DO UPDATE SET
            ensemble_score = EXCLUDED.ensemble_score,
            severity = EXCLUDED.severity;
        """

        values = []
        for ar, meta in zip(anomalies, metadata):
            values.append((
                ar.anomaly_id, ar.record_id, ar.detection_method,
                ar.severity.value if hasattr(ar.severity, 'value') else ar.severity,
                ar.z_score, ar.expected_cost, ar.actual_cost, ar.deviation_pct,
                ar.detected_at,
                json.dumps(ar.shap_attribution) if ar.shap_attribution else None,
                meta["cloud_provider"], meta["service"], meta["account_id"],
                meta["usage_date"],
                meta.get("zscore_score"), meta.get("iforest_score"),
                meta.get("lstm_score"), meta["ensemble_score"]
            ))

        total = 0
        batch_size = 1000
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(values), batch_size):
                    batch = values[i:i + batch_size]
                    psycopg2.extras.execute_values(cur, query, batch, page_size=1000)
                    total += cur.rowcount
        return total

    def get_anomalies(
        self,
        cloud_provider: Optional[str] = None,
        service: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_severity: Optional[str] = None,
        limit: int = 1000
    ) -> List[dict]:
        """
        Query anomalies table with optional filters.
        Returns list of dicts (raw rows, not AnomalyResult objects).
        """
        query = "SELECT * FROM anomalies WHERE 1=1"
        params = []

        if cloud_provider:
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)
        if service:
            query += " AND service = %s"
            params.append(service)
        if start_date:
            query += " AND usage_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND usage_date <= %s"
            params.append(end_date)
        
        if min_severity:
            # min_severity maps to: low=0.3, medium=0.5, high=0.7, critical=0.9
            # Since severity is a string ('low', 'medium', 'high', 'critical'), 
            # we should instead filter using the ensemble_score threshold if severity filtering is needed by value,
            # but usually it's just a direct severity check, or we can resolve it via score.
            # Assuming min_severity maps to scores based on config.
            from detection import config
            if min_severity in config.SEVERITY_THRESHOLDS:
                threshold = config.SEVERITY_THRESHOLDS[min_severity]
                query += " AND ensemble_score >= %s"
                params.append(threshold)

        query += " ORDER BY usage_date DESC, ensemble_score DESC LIMIT %s"
        params.append(limit)

        results = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    results.append(dict(row))
        return results

    # ── Forecasting ────────────────────────────────────────────

    def write_forecasts(self, forecasts: List[ForecastResult], metadata: List[dict]) -> int:
        """
        Bulk upsert forecast rows.
        metadata list items: {prophet_prediction, lgbm_prediction, prophet_weight, lgbm_weight}
        ON CONFLICT on (cloud_provider, service, horizon_days, forecast_date, model_used) DO UPDATE
        SET predicted_cost=EXCLUDED.predicted_cost,
            lower_bound=EXCLUDED.lower_bound,
            upper_bound=EXCLUDED.upper_bound.
        Returns count of rows written.
        """
        if not forecasts:
            return 0

        query = """
        INSERT INTO forecasts (
            forecast_id, cloud_provider, service, region, horizon_days,
            forecast_date, predicted_cost, lower_bound, upper_bound,
            model_used, generated_at, prophet_prediction, lgbm_prediction,
            prophet_weight, lgbm_weight
        ) VALUES %s
        ON CONFLICT (cloud_provider, service, horizon_days, forecast_date, model_used) DO UPDATE SET
            predicted_cost = EXCLUDED.predicted_cost,
            lower_bound = EXCLUDED.lower_bound,
            upper_bound = EXCLUDED.upper_bound;
        """

        values = []
        for fr, meta in zip(forecasts, metadata):
            values.append((
                fr.forecast_id, fr.cloud_provider.value if hasattr(fr.cloud_provider, 'value') else fr.cloud_provider, 
                fr.service, fr.region, fr.horizon_days,
                fr.forecast_date, fr.predicted_cost, fr.lower_bound, fr.upper_bound,
                fr.model_used, fr.generated_at,
                meta.get("prophet_prediction"), meta.get("lgbm_prediction"),
                meta.get("prophet_weight"), meta.get("lgbm_weight")
            ))

        total = 0
        batch_size = 1000
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(values), batch_size):
                    batch = values[i:i + batch_size]
                    psycopg2.extras.execute_values(cur, query, batch, page_size=1000)
                    total += cur.rowcount
        return total

    def get_forecasts(
        self,
        cloud_provider: Optional[str] = None,
        service: Optional[str] = None,
        horizon_days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        model_used: str = "ensemble"
    ) -> List[dict]:
        """Returns forecast rows matching filters, ordered by forecast_date ASC."""
        query = "SELECT * FROM forecasts WHERE model_used = %s"
        params = [model_used]

        if cloud_provider:
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)
        if service:
            query += " AND service = %s"
            params.append(service)
        if horizon_days is not None:
            query += " AND horizon_days = %s"
            params.append(horizon_days)
        if start_date:
            query += " AND forecast_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND forecast_date <= %s"
            params.append(end_date)

        query += " ORDER BY forecast_date ASC"

        results = []
        with DatabaseManager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    results.append(dict(row))
        return results

