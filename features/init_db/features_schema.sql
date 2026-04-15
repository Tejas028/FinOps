-- ── Spend features table ──────────────────────────────────────
-- One row per (date x cloud x service_category x account_id x environment x team).
-- Populated by FeatureEngineeringPipeline.

CREATE TABLE IF NOT EXISTS spend_features (

    -- Partition + identity
    feature_date        DATE        NOT NULL,
    cloud_provider      TEXT        NOT NULL,
    service_category    TEXT        NOT NULL,
    account_id          TEXT        NOT NULL,
    environment         TEXT        NOT NULL DEFAULT 'unknown',
    team                TEXT        NOT NULL DEFAULT 'unknown',

    -- Raw spend (from daily_aggregates)
    total_cost_usd      DOUBLE PRECISION NOT NULL,
    record_count        INTEGER     NOT NULL,

    -- Lag features
    cost_lag_1d         DOUBLE PRECISION,   -- spend D-1
    cost_lag_7d         DOUBLE PRECISION,   -- spend D-7
    cost_lag_30d        DOUBLE PRECISION,   -- spend D-30

    -- Rolling statistics (trailing windows ending at feature_date)
    rolling_mean_7d     DOUBLE PRECISION,
    rolling_std_7d      DOUBLE PRECISION,
    rolling_mean_30d    DOUBLE PRECISION,
    rolling_std_30d     DOUBLE PRECISION,

    -- Change ratios (percentage change vs lag)
    pct_change_1d       DOUBLE PRECISION,   -- (today - D-1) / D-1
    pct_change_7d       DOUBLE PRECISION,   -- (today - D-7) / D-7
    pct_change_30d      DOUBLE PRECISION,   -- (today - D-30) / D-30

    -- Anomaly signal
    -- (total_cost_usd - rolling_mean_30d) / rolling_std_30d
    -- NULL if rolling_std_30d is 0 or NULL (not enough history)
    z_score_30d         DOUBLE PRECISION,

    -- Cyclical / calendar features (for forecasting)
    day_of_week         INTEGER,    -- 0=Monday ... 6=Sunday
    day_of_month        INTEGER,    -- 1-31
    week_of_year        INTEGER,    -- 1-53
    month               INTEGER,    -- 1-12
    is_weekend          BOOLEAN,
    is_month_start      BOOLEAN,    -- day_of_month == 1
    is_month_end        BOOLEAN,    -- last day of month

    -- Metadata
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (feature_date, cloud_provider, service_category,
                 account_id, environment, team)
);

-- Convert to hypertable
SELECT create_hypertable(
    'spend_features',
    'feature_date',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Indexes for downstream query patterns
CREATE INDEX IF NOT EXISTS idx_feat_cloud_date
    ON spend_features (cloud_provider, feature_date DESC);

CREATE INDEX IF NOT EXISTS idx_feat_service_date
    ON spend_features (service_category, feature_date DESC);

CREATE INDEX IF NOT EXISTS idx_feat_zscore
    ON spend_features (z_score_30d DESC NULLS LAST)
    WHERE z_score_30d IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_feat_account_date
    ON spend_features (account_id, feature_date DESC);
