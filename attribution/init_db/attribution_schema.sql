CREATE TABLE IF NOT EXISTS cost_attributions (
    attribution_date    DATE            NOT NULL,
    cloud_provider      TEXT            NOT NULL,
    service_category    TEXT            NOT NULL,
    account_id          TEXT            NOT NULL,
    environment         TEXT            NOT NULL DEFAULT 'unknown',
    team                TEXT            NOT NULL DEFAULT 'unknown',

    -- Total cost on this date for this group
    total_cost_usd      DOUBLE PRECISION NOT NULL,

    -- Top SHAP drivers (stored as JSONB — key: feature_name, value: shap_value)
    -- Example: {"cost_lag_7d": 42.3, "rolling_mean_30d": -12.1, "is_weekend": 5.2}
    shap_values         JSONB           NOT NULL,

    -- Top 3 drivers by absolute SHAP (for fast API queries)
    top_driver_1        TEXT,           -- feature name
    top_driver_1_value  DOUBLE PRECISION,
    top_driver_2        TEXT,
    top_driver_2_value  DOUBLE PRECISION,
    top_driver_3        TEXT,
    top_driver_3_value  DOUBLE PRECISION,

    -- Model metadata
    model_r2_score      DOUBLE PRECISION,
    feature_count       INTEGER,
    computed_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    PRIMARY KEY (attribution_date, cloud_provider, service_category,
                 account_id, environment, team)
);

SELECT create_hypertable(
    'cost_attributions', 'attribution_date',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_attr_cloud_date
    ON cost_attributions (cloud_provider, attribution_date DESC);

CREATE INDEX IF NOT EXISTS idx_attr_service_date
    ON cost_attributions (service_category, attribution_date DESC);

CREATE INDEX IF NOT EXISTS idx_attr_top_driver
    ON cost_attributions (top_driver_1, attribution_date DESC);

CREATE INDEX IF NOT EXISTS idx_attr_shap_gin
    ON cost_attributions USING GIN (shap_values);
