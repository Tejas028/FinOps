-- ── Forecasting Table ──────────────────────────────────────────
-- Stores future cost predictions from the ensemble forecaster.

CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id         TEXT        PRIMARY KEY,
    
    -- Dimensions
    cloud_provider      TEXT        NOT NULL,
    service             TEXT        NOT NULL,
    region              TEXT        NOT NULL,
    
    -- Time Context
    horizon_days        INTEGER     NOT NULL,   -- e.g., 7, 30, 90
    forecast_date       DATE        NOT NULL,   -- The date being predicted
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Predictions
    predicted_cost      DOUBLE PRECISION NOT NULL,
    lower_bound         DOUBLE PRECISION,       -- For confidence intervals
    upper_bound         DOUBLE PRECISION,
    
    -- Model Metadata
    model_used          TEXT        NOT NULL,   -- 'ensemble' | 'prophet' | 'lgbm'
    prophet_prediction  DOUBLE PRECISION,
    lgbm_prediction     DOUBLE PRECISION,
    prophet_weight      DOUBLE PRECISION,
    lgbm_weight         DOUBLE PRECISION,
    
    -- Ensure we don't store multiple ensemble forecasts for same date/group/model
    UNIQUE (cloud_provider, service, horizon_days, forecast_date, model_used)
);

-- ── Indexes ──────────────────────────────────────────────────
-- Main dashboard lookup for trend forecasting
CREATE INDEX IF NOT EXISTS idx_forecasts_lookup 
    ON forecasts (cloud_provider, service, forecast_date ASC);

-- Clean-up index for old forecasts
CREATE INDEX IF NOT EXISTS idx_forecasts_generated 
    ON forecasts (generated_at DESC);
