import os

FORECAST_HORIZONS = [7, 14, 30, 90]    # days into the future

# ─── Prophet ─────────────────────────────────────────────────
PROPHET_CHANGEPOINT_PRIOR_SCALE   = 0.05
PROPHET_SEASONALITY_PRIOR_SCALE   = 10.0
PROPHET_YEARLY_SEASONALITY         = True
PROPHET_WEEKLY_SEASONALITY         = True
PROPHET_DAILY_SEASONALITY          = False
PROPHET_INTERVAL_WIDTH             = 0.95   # for confidence bands
PROPHET_MCMC_SAMPLES               = 0      # 0 = MAP (fast), >0 = full Bayes

# ─── LightGBM ────────────────────────────────────────────────
LGBM_N_ESTIMATORS                  = 500
LGBM_LEARNING_RATE                 = 0.05
LGBM_NUM_LEAVES                    = 31
LGBM_MAX_DEPTH                     = -1
LGBM_EARLY_STOPPING_ROUNDS         = 20
LGBM_EVAL_METRIC                   = "mae"
LGBM_RANDOM_STATE                  = 42
LGBM_FEATURE_COLS = [
    "lag_1d", "lag_7d", "lag_30d",
    "rolling_mean_7d", "rolling_mean_30d",
    "rolling_std_7d", "rolling_std_30d",
    "pct_change_7d", "day_of_week",
    "is_weekend", "is_month_end",
    "month", "quarter"
]

# ─── Training Split ──────────────────────────────────────────
TRAIN_RATIO    = 0.70
VAL_RATIO      = 0.15
TEST_RATIO     = 0.15

# ─── Ensemble ────────────────────────────────────────────────
ENSEMBLE_PROPHET_WEIGHT_DEFAULT  = 0.45
ENSEMBLE_LGBM_WEIGHT_DEFAULT     = 0.55

# ─── Model Registry ──────────────────────────────────────────
MODEL_REGISTRY_PATH  = "forecasting/model_registry"
MIN_ROWS_FOR_PROPHET = 60    # Prophet needs at least 2 months
MIN_ROWS_FOR_LGBM    = 45

# Ensure registry exists
os.makedirs(MODEL_REGISTRY_PATH, exist_ok=True)
