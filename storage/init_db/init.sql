-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ── Main billing records table ────────────────────────────────
CREATE TABLE IF NOT EXISTS billing_records (
    -- Identity
    record_id           TEXT        NOT NULL,
    fingerprint         TEXT        NOT NULL,

    -- Source
    cloud_provider      TEXT        NOT NULL,   -- 'aws' | 'azure' | 'gcp'
    account_id          TEXT        NOT NULL,
    service_name_raw    TEXT        NOT NULL,
    service_category    TEXT        NOT NULL,   -- normalized category
    region              TEXT        NOT NULL,
    resource_id         TEXT,

    -- Time (partition key — MUST be first in PRIMARY KEY for hypertable)
    usage_date          DATE        NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Cost
    cost_original       DOUBLE PRECISION NOT NULL,
    currency_original   TEXT        NOT NULL,
    cost_usd            DOUBLE PRECISION NOT NULL,
    usage_quantity      DOUBLE PRECISION,
    usage_unit          TEXT,

    -- Tags (stored as JSONB for queryability)
    tags_raw            TEXT,
    tags                JSONB,

    -- Enrichment
    environment         TEXT,
    team                TEXT,

    -- Anomaly (populated later by Module 6)
    anomaly_flag        BOOLEAN     NOT NULL DEFAULT FALSE,
    anomaly_severity    TEXT,

    PRIMARY KEY (usage_date, fingerprint)
);

-- Convert to TimescaleDB hypertable, partitioned by usage_date
-- chunk_time_interval = 7 days (weekly chunks for billing granularity)
SELECT create_hypertable(
    'billing_records',
    'usage_date',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ── Indexes ───────────────────────────────────────────────────
-- Most common query patterns:
CREATE INDEX IF NOT EXISTS idx_cloud_date
    ON billing_records (cloud_provider, usage_date DESC);

CREATE INDEX IF NOT EXISTS idx_service_date
    ON billing_records (service_category, usage_date DESC);

CREATE INDEX IF NOT EXISTS idx_account_date
    ON billing_records (account_id, usage_date DESC);

CREATE INDEX IF NOT EXISTS idx_environment
    ON billing_records (environment, usage_date DESC);

CREATE INDEX IF NOT EXISTS idx_team
    ON billing_records (team, usage_date DESC);

-- JSONB index for tag queries
CREATE INDEX IF NOT EXISTS idx_tags_gin
    ON billing_records USING GIN (tags);

-- ── Daily aggregates table ────────────────────────────────────
-- Pre-computed rollups used by forecasting + dashboard APIs.
-- Populated by StorageClient.refresh_daily_aggregates()

CREATE TABLE IF NOT EXISTS daily_aggregates (
    agg_date            DATE        NOT NULL,
    cloud_provider      TEXT        NOT NULL,
    service_category    TEXT        NOT NULL,
    account_id          TEXT        NOT NULL,
    environment         TEXT,
    team                TEXT,

    total_cost_usd      DOUBLE PRECISION NOT NULL,
    record_count        INTEGER     NOT NULL,
    avg_cost_usd        DOUBLE PRECISION NOT NULL,

    PRIMARY KEY (agg_date, cloud_provider, service_category, account_id, environment, team)
);

CREATE INDEX IF NOT EXISTS idx_agg_date_cloud
    ON daily_aggregates (agg_date DESC, cloud_provider);

CREATE INDEX IF NOT EXISTS idx_agg_service
    ON daily_aggregates (service_category, agg_date DESC);

-- ── Ingestion audit log ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingestion_log (
    log_id              SERIAL      PRIMARY KEY,
    run_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cloud_provider      TEXT        NOT NULL,
    records_inserted    INTEGER     NOT NULL,
    records_skipped     INTEGER     NOT NULL,
    date_range_start    DATE        NOT NULL,
    date_range_end      DATE        NOT NULL,
    duration_seconds    DOUBLE PRECISION,
    status              TEXT        NOT NULL,   -- 'success' | 'error'
    error_message       TEXT
);
