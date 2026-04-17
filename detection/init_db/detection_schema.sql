-- ── Anomaly Detection Table ─────────────────────────────────────
-- Stores high-confidence anomalies detected by the ensemble engine.

CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id          TEXT        PRIMARY KEY,
    record_id           TEXT,       -- Can be NULL for aggregated anomalies
    
    -- Detection Metadata
    detection_method    TEXT        NOT NULL,   -- e.g., 'ensemble'
    severity            TEXT        NOT NULL,   -- 'low' | 'medium' | 'high' | 'critical'
    
    -- Metrics
    z_score             DOUBLE PRECISION,       -- Statistical deviation
    expected_cost       DOUBLE PRECISION NOT NULL,
    actual_cost         DOUBLE PRECISION NOT NULL,
    deviation_pct       DOUBLE PRECISION NOT NULL,
    
    -- Audit
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- AI Context
    shap_attribution    JSONB,      -- Factor contribution weights for explanation
    
    -- Context/Dimensions (for fast join-less lookups)
    cloud_provider      TEXT        NOT NULL,
    service             TEXT        NOT NULL,
    account_id          TEXT        NOT NULL,
    usage_date          DATE        NOT NULL,
    
    -- Ensemble Scorer Details
    zscore_score        DOUBLE PRECISION,       -- Raw score from Z-Score (0-1)
    iforest_score       DOUBLE PRECISION,       -- Raw score from IsolationForest (0-1)
    lstm_score          DOUBLE PRECISION,       -- Raw score from LSTM (0-1)
    ensemble_score      DOUBLE PRECISION NOT NULL -- Weighted final score (0-1)
);

-- ── Indexes ──────────────────────────────────────────────────
-- Primary daily summary lookup
CREATE INDEX IF NOT EXISTS idx_anomalies_date 
    ON anomalies (usage_date DESC, cloud_provider);

-- Severity-based grouping for alerts
CREATE INDEX IF NOT EXISTS idx_anomalies_severity
    ON anomalies (severity, usage_date DESC);

-- Service-based cost attribution lookup
CREATE INDEX IF NOT EXISTS idx_anomalies_service
    ON anomalies (service, usage_date DESC);
