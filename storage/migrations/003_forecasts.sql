CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id         TEXT        NOT NULL,
    cloud_provider      TEXT        NOT NULL,
    service             TEXT        NOT NULL,
    region              TEXT,
    horizon_days        INT         NOT NULL,   -- 7 | 14 | 30 | 90
    forecast_date       DATE        NOT NULL,   -- the predicted future date
    predicted_cost      FLOAT       NOT NULL,
    lower_bound         FLOAT       NOT NULL,
    upper_bound         FLOAT       NOT NULL,
    model_used          TEXT        NOT NULL,   -- 'prophet'|'lightgbm'|'ensemble'
    generated_at        TIMESTAMPTZ NOT NULL,
    -- internal metadata
    prophet_prediction  FLOAT,
    lgbm_prediction     FLOAT,
    prophet_weight      FLOAT,
    lgbm_weight         FLOAT,
    PRIMARY KEY (forecast_id, forecast_date)
);

SELECT create_hypertable('forecasts', 'forecast_date',
    if_not_exists => TRUE);

CREATE UNIQUE INDEX IF NOT EXISTS idx_forecasts_unique
    ON forecasts(cloud_provider, service, horizon_days, forecast_date, model_used);
CREATE INDEX IF NOT EXISTS idx_forecasts_cloud
    ON forecasts(cloud_provider, service);
