CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id          TEXT        NOT NULL,
    record_id           TEXT        NOT NULL,
    detection_method    TEXT        NOT NULL,
    severity            TEXT        NOT NULL,
    z_score             FLOAT,
    expected_cost       FLOAT       NOT NULL,
    actual_cost         FLOAT       NOT NULL,
    deviation_pct       FLOAT       NOT NULL,
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    shap_attribution    JSONB,
    cloud_provider      TEXT        NOT NULL,
    service             TEXT        NOT NULL,
    account_id          TEXT        NOT NULL,
    usage_date          DATE        NOT NULL,
    zscore_score        FLOAT,
    iforest_score       FLOAT,
    lstm_score          FLOAT,
    ensemble_score      FLOAT       NOT NULL,
    PRIMARY KEY (anomaly_id)
);

SELECT create_hypertable('anomalies', 'detected_at', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_anomalies_record ON anomalies(record_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_cloud ON anomalies(cloud_provider, service);
CREATE INDEX IF NOT EXISTS idx_anomalies_date ON anomalies(usage_date DESC);
