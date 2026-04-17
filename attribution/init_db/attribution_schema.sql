-- ── Cost Attribution Table ─────────────────────────────────────
-- Stores SHAP-based driver analysis for cost changes.

CREATE TABLE IF NOT EXISTS cost_attributions (
    attribution_date    DATE        NOT NULL,
    cloud_provider      TEXT        NOT NULL,
    service_category    TEXT        NOT NULL,
    account_id          TEXT        NOT NULL,
    environment         TEXT        NOT NULL,
    team                TEXT        NOT NULL,
    
    -- Main metric
    total_cost_usd      DOUBLE PRECISION NOT NULL,
    
    -- AI Details
    shap_values         JSONB       NOT NULL,   -- Complete contribution map
    
    -- Top Drivers (denormalized for fast filtering)
    top_driver_1        TEXT,
    top_driver_1_value  DOUBLE PRECISION,
    top_driver_2        TEXT,
    top_driver_2_value  DOUBLE PRECISION,
    top_driver_3        TEXT,
    top_driver_3_value  DOUBLE PRECISION,
    
    -- Model metrics
    model_r2_score      DOUBLE PRECISION,
    feature_count       INTEGER,
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    PRIMARY KEY (attribution_date, cloud_provider, service_category, account_id, environment, team)
);

-- ── Indexes ──────────────────────────────────────────────────
-- Main dashboard driver breakdown query
CREATE INDEX IF NOT EXISTS idx_attribution_lookup
    ON cost_attributions (attribution_date DESC, cloud_provider, service_category);

-- Driver-specific filtering
CREATE INDEX IF NOT EXISTS idx_attribution_driver
    ON cost_attributions (top_driver_1);
