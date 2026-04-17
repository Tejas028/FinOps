import time
from datetime import date
from typing import Optional, List
import copy

from alerting.rules import AlertRulesEngine
from alerting.repository import AlertRepository
from alerting import config
from shared.schemas.alert import Alert
from storage.db import DatabaseManager
import psycopg2.extras

class AlertingEngine:
    def __init__(self):
        self.rules_engine = AlertRulesEngine()
        self.repository = AlertRepository()

    def run(
        self,
        start_date: date,
        end_date: date,
        cloud_provider: Optional[str] = None,
        monthly_budget_usd: Optional[float] = None
    ) -> dict:
        t0 = time.time()
        
        all_alerts: List[Alert] = []

        # Step 1: Query anomalies
        anomaly_query = "SELECT * FROM anomalies WHERE usage_date BETWEEN %s AND %s"
        params = [start_date, end_date]
        if cloud_provider and cloud_provider != "all":
            anomaly_query += " AND cloud_provider = %s"
            params.append(cloud_provider)

        anomaly_alerts = 0
        with DatabaseManager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(anomaly_query, tuple(params))
                anomalies = cur.fetchall()
                for anomaly in anomalies:
                    # In a real system we'd join billing context if needed, but expected_cost is on the anomaly row
                    alert = self.rules_engine.evaluate_anomaly(dict(anomaly), {})
                    if alert:
                        all_alerts.append(alert)
                        anomaly_alerts += 1

        # Step 2: Query spend_features for spend_spike
        features_query = "SELECT * FROM spend_features WHERE feature_date BETWEEN %s AND %s AND abs(pct_change_1d) > %s"
        f_params = [start_date, end_date, config.SPEND_SPIKE_PCT_THRESHOLD]
        if cloud_provider and cloud_provider != "all":
            features_query += " AND cloud_provider = %s"
            f_params.append(cloud_provider)
            
        spend_spike_alerts = 0
        with DatabaseManager.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(features_query, tuple(f_params))
                features = cur.fetchall()
                for feature in features:
                    alert = self.rules_engine.evaluate_spend_spike(dict(feature))
                    if alert:
                        all_alerts.append(alert)
                        spend_spike_alerts += 1

        # Step 3: Budget risks
        budget_alerts = 0
        if monthly_budget_usd is not None and monthly_budget_usd > 0:
            forecasts_query = "SELECT * FROM forecasts WHERE forecast_date BETWEEN %s AND %s AND model_used = 'ensemble'"
            fc_params = [start_date, end_date]
            if cloud_provider and cloud_provider != "all":
                forecasts_query += " AND cloud_provider = %s"
                fc_params.append(cloud_provider)
            
            # For simplicity, calculate projected monthly cost per cloud. 
            # Sum up predicted_cost to get projected for the month if we group by cloud
            
            # Since forecasts has multiple horizon items per date, 
            # let's just use the horizon_days = 30 and most recent forecast date in the range per cloud
            risk_query = """
                SELECT cloud_provider, SUM(predicted_cost) as proj
                FROM forecasts 
                WHERE forecast_date BETWEEN %s AND %s
                  AND horizon_days = 30
                  AND model_used = 'ensemble'
            """
            rq_params = [start_date, end_date]
            if cloud_provider and cloud_provider != "all":
                risk_query += " AND cloud_provider = %s"
                rq_params.append(cloud_provider)
            risk_query += " GROUP BY cloud_provider"

            with DatabaseManager.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(risk_query, tuple(rq_params))
                    risks = cur.fetchall()
                    for risk in risks:
                        cloud = risk['cloud_provider']
                        proj = float(risk['proj'])
                        # Here, in a real scenario, projected monthly cost would be sum(month-to-date) + sum(predicted remaining days).
                        # We just take proj directly for this prompt's requirement.
                        alert = self.rules_engine.evaluate_budget_breach(
                            cloud_provider=cloud,
                            projected_monthly_cost=proj,
                            monthly_budget_usd=monthly_budget_usd,
                            breach_date=None
                        )
                        if alert:
                            all_alerts.append(alert)
                            budget_alerts += 1

        # Step 4: Deduplicate matches already in DB before insert
        deduped_alerts = []
        total_skipped = 0

        # Create lookup keys for db check
        # We can query all alerts in the date range to check for duplicates
        db_alerts_lookup = set()
        existing_alerts_query = "SELECT alert_type, cloud_provider, service_category, alert_date FROM alerts WHERE alert_date BETWEEN %s AND %s"
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(existing_alerts_query, (start_date, end_date))
                for row in cur.fetchall():
                    # (alert_type, cloud_provider, service_category, alert_date)
                    k = (row[0], row[1], row[2], str(row[3]))
                    db_alerts_lookup.add(k)
        
        # Deduplicate internally first
        internal_lookup = set()
        
        for a in all_alerts:
            k = (a.alert_type, a.cloud_provider, a.service_category, str(a.alert_date))
            if k in db_alerts_lookup or k in internal_lookup:
                total_skipped += 1
            else:
                deduped_alerts.append(a)
                internal_lookup.add(k)

        # Step 5: Insert
        total_inserted = self.repository.insert_alerts(deduped_alerts)

        return {
            "anomaly_alerts": anomaly_alerts,
            "spend_spike_alerts": spend_spike_alerts,
            "budget_alerts": budget_alerts,
            "total_inserted": total_inserted,
            "total_skipped": total_skipped,
            "duration_seconds": time.time() - t0
        }
