import json
import psycopg2.extras
from typing import List, Tuple, Dict, Optional
from datetime import date
from storage.db import DatabaseManager
from shared.schemas.alert import Alert

class AlertRepository:

    def insert_alerts(self, alerts: List[Alert]) -> int:
        """
        Bulk insert into alerts table.
        ON CONFLICT (alert_date, alert_id) DO NOTHING.
        Use execute_values() in batches of 500.
        Returns rows inserted.
        """
        if not alerts:
            return 0

        query = """
        INSERT INTO alerts (
            alert_id, alert_type, severity, cloud_provider, service_category,
            account_id, alert_date, title, message, metadata,
            is_resolved, resolved_at
        ) VALUES %s
        ON CONFLICT (alert_date, alert_id) DO NOTHING;
        """

        values = []
        for a in alerts:
            values.append((
                a.alert_id,
                a.alert_type,
                a.severity,
                a.cloud_provider,
                a.service_category,
                a.account_id,
                a.alert_date,
                a.title,
                a.message,
                json.dumps(a.metadata) if a.metadata else None,
                a.is_resolved,
                a.resolved_at
            ))

        total_inserted = 0
        batch_size = 500
        
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(values), batch_size):
                    batch = values[i:i + batch_size]
                    psycopg2.extras.execute_values(cur, query, batch, page_size=batch_size)
                    total_inserted += cur.rowcount
                    
        return total_inserted

    def get_alerts(
        self,
        start_date: date,
        end_date: date,
        severity: Optional[str] = None,
        cloud_provider: Optional[str] = None,
        alert_type: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Alert], int]:
        """
        Returns (alerts, total_count) for pagination.
        """
        base_query = "FROM alerts WHERE alert_date BETWEEN %s AND %s"
        params = [start_date, end_date]

        if severity and severity != "all":
            base_query += " AND severity = %s"
            params.append(severity)
        if cloud_provider and cloud_provider != "all":
            base_query += " AND cloud_provider = %s"
            params.append(cloud_provider)
        if alert_type and alert_type != "all":
            base_query += " AND alert_type = %s"
            params.append(alert_type)
        if is_resolved is not None:
            base_query += " AND is_resolved = %s"
            params.append(is_resolved)

        count_query = f"SELECT COUNT(*) {base_query}"
        data_query = f"SELECT * {base_query} ORDER BY alert_date DESC, created_at DESC LIMIT %s OFFSET %s"
        
        data_params = params + [limit, offset]

        alerts = []
        total_count = 0

        with DatabaseManager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(count_query, tuple(params))
                total_count = cur.fetchone()['count']

                cur.execute(data_query, tuple(data_params))
                for row in cur.fetchall():
                    alerts.append(Alert(**row))

        return alerts, total_count

    def resolve_alert(self, alert_id: str) -> bool:
        """
        UPDATE alerts SET is_resolved=TRUE, resolved_at=NOW()
        WHERE alert_id = %s
        Returns True if row updated.
        """
        query = "UPDATE alerts SET is_resolved=TRUE, resolved_at=NOW() WHERE alert_id = %s AND is_resolved = FALSE"
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (alert_id,))
                return cur.rowcount > 0

    def get_unresolved_count(self, start_date: Optional[date] = None, end_date: Optional[date] = None, cloud_provider: Optional[str] = None) -> Dict[str, int]:
        """
        SELECT severity, COUNT(*) FROM alerts
        WHERE is_resolved = FALSE
        ...
        GROUP BY severity
        Returns {"low": N, "medium": N, "high": N, "critical": N}
        """
        counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        query = "SELECT severity, COUNT(*) FROM alerts WHERE is_resolved = FALSE"
        params = []
        
        if start_date:
            query += " AND alert_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND alert_date <= %s"
            params.append(end_date)
        if cloud_provider and cloud_provider != "all":
            query += " AND cloud_provider = %s"
            params.append(cloud_provider)

        query += " GROUP BY severity"
        
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                for row in cur.fetchall():
                    sev = row[0]
                    cnt = row[1]
                    if sev in counts:
                        counts[sev] = cnt

        return counts
