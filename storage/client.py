import time
import json
import psycopg2.extras
from typing import List, Optional, Dict, Any
from datetime import date

from shared.schemas.normalized import NormalizedRecord
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
        fingerprints: List[str],
        anomaly_flag: bool,
        anomaly_severity: Optional[str]
    ) -> int:
        
        if not fingerprints:
            return 0
            
        query = """
        UPDATE billing_records
        SET anomaly_flag = %s, anomaly_severity = %s
        WHERE fingerprint IN %s
        """
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (anomaly_flag, anomaly_severity, tuple(fingerprints)))
                return cur.rowcount
