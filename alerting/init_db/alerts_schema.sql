CREATE TABLE IF NOT EXISTS alerts (
    alert_id        TEXT        NOT NULL DEFAULT gen_random_uuid()::text,
    alert_type      TEXT        NOT NULL,
    -- "anomaly_detected" | "budget_breach_imminent" |
    -- "spend_spike" | "forecast_exceeded"
    severity        TEXT        NOT NULL,
    -- "low" | "medium" | "high" | "critical"
    cloud_provider  TEXT        NOT NULL,
    service_category TEXT,
    account_id      TEXT,
    alert_date      DATE        NOT NULL,
    title           TEXT        NOT NULL,
    message         TEXT        NOT NULL,
    metadata        JSONB,
    -- arbitrary context: z_score, deviation_pct, budget, etc.
    is_resolved     BOOLEAN     NOT NULL DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (alert_date, alert_id)
);

SELECT create_hypertable(
    'alerts', 'alert_date',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_alerts_severity
    ON alerts (severity, alert_date DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_cloud
    ON alerts (cloud_provider, alert_date DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved
    ON alerts (is_resolved, alert_date DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type
    ON alerts (alert_type, alert_date DESC);
