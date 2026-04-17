from typing import Optional
from shared.schemas.alert import Alert
from alerting import config
from datetime import date

class AlertRulesEngine:
    def evaluate_anomaly(self, anomaly: dict, billing_context: dict) -> Optional[Alert]:
        severity = anomaly.get('severity', 'low')
        service = anomaly.get('service', 'unknown service')
        usage_date = anomaly.get('usage_date')
        
        if isinstance(usage_date, str):
            usage_date_obj = date.fromisoformat(usage_date)
        elif isinstance(usage_date, date):
            usage_date_obj = usage_date
        else:
            usage_date_obj = date.today()

        deviation_pct = anomaly.get('deviation_pct', 0.0)
        actual_cost = anomaly.get('actual_cost', 0.0)
        expected_cost = anomaly.get('expected_cost', 0.0)

        # Logic to differentiate between spike and drop
        if deviation_pct < 0:
            anomaly_type = "drop"
            direction_label = "below"
        else:
            anomaly_type = "spike"
            direction_label = "above"

        title = f"Anomaly: {service} spend {anomaly_type} on {usage_date_obj}"
        message = f"Detected {abs(deviation_pct):.1f}% {direction_label} expected cost (${actual_cost:.2f} vs ${expected_cost:.2f})"
        
        metadata = {
            "z_score": anomaly.get('z_score', 0.0),
            "deviation_pct": deviation_pct,
            "detection_method": anomaly.get('detection_method', 'ensemble'),
            "actual_cost": actual_cost,
            "expected_cost": expected_cost,
            "anomaly_direction": anomaly_type
        }

        return Alert(
            alert_type="anomaly_detected",
            severity=severity,
            cloud_provider=anomaly.get('cloud_provider', 'unknown'),
            service_category=service,
            account_id=anomaly.get('account_id'),
            alert_date=usage_date_obj,
            title=title,
            message=message,
            metadata=metadata
        )

    def evaluate_spend_spike(self, feature_row: dict) -> Optional[Alert]:
        """
        Triggered per spend_features row where ABS(pct_change_1d) > SPEND_SPIKE_PCT_THRESHOLD.
        severity: "high" if pct_change > 100%, else "medium"
        title: "{cloud} {service} spend up {pct:.0f}% day-over-day"
        alert_type: "spend_spike"
        """
        pct_change = feature_row.get('pct_change_1d', 0.0)
        if pct_change is None:
            pct_change = 0.0
            
        if abs(pct_change) > config.SPEND_SPIKE_PCT_THRESHOLD:
            severity = "high" if abs(pct_change) > 100.0 else "medium"
            cloud = feature_row.get('cloud_provider', 'unknown')
            service = feature_row.get('service_category', 'unknown')
            
            usage_date = feature_row.get('feature_date')
            if isinstance(usage_date, str):
                usage_date_obj = date.fromisoformat(usage_date)
            elif isinstance(usage_date, date):
                usage_date_obj = usage_date
            else:
                usage_date_obj = date.today()

            title = f"{cloud} {service} spend up {pct_change:.0f}% day-over-day"
            message = title
            metadata = {
                "pct_change_1d": pct_change,
                "total_cost_usd": feature_row.get('total_cost_usd', 0.0),
                "rolling_mean_7d": feature_row.get('rolling_mean_7d', 0.0)
            }

            return Alert(
                alert_type="spend_spike",
                severity=severity,
                cloud_provider=cloud,
                service_category=service,
                account_id=feature_row.get('account_id'),
                alert_date=usage_date_obj,
                title=title,
                message=message,
                metadata=metadata
            )
        return None

    def evaluate_budget_breach(
        self,
        cloud_provider: str,
        projected_monthly_cost: float,
        monthly_budget_usd: float,
        breach_date: Optional[str]
    ) -> Optional[Alert]:
        """
        pct_used = projected / budget * 100
        If pct_used >= BUDGET_BREACH_PCT:
            severity = "critical"
            title = "{cloud} budget breach projected by {breach_date}"
        elif pct_used >= BUDGET_WARNING_PCT:
            severity = "high"
            title = "{cloud} budget at {pct_used:.0f}% - breach risk"
        Else: return None
        alert_type: "budget_breach_imminent"
        metadata: { projected, budget, pct_used, breach_date }
        """
        if monthly_budget_usd <= 0:
            return None

        pct_used = (projected_monthly_cost / monthly_budget_usd) * 100.0

        severity = None
        title = ""

        if pct_used >= config.BUDGET_BREACH_PCT:
            severity = "critical"
            title = f"{cloud_provider} budget breach projected by {breach_date or 'end of month'}"
        elif pct_used >= config.BUDGET_WARNING_PCT:
            severity = "high"
            title = f"{cloud_provider} budget at {pct_used:.0f}% - breach risk"

        if severity:
            metadata = {
                "projected": projected_monthly_cost,
                "budget": monthly_budget_usd,
                "pct_used": pct_used,
                "breach_date": breach_date
            }
            return Alert(
                alert_type="budget_breach_imminent",
                severity=severity,
                cloud_provider=cloud_provider,
                service_category=None,
                account_id=None,
                alert_date=date.today(),
                title=title,
                message=title,
                metadata=metadata
            )
        return None
