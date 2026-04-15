import os

SHAP_FEATURE_COLUMNS = [
    "cost_lag_1d", "cost_lag_7d", "cost_lag_30d",
    "rolling_mean_7d", "rolling_std_7d",
    "rolling_mean_30d", "rolling_std_30d",
    "pct_change_1d", "pct_change_7d", "pct_change_30d",
    "z_score_30d",
    "day_of_week", "day_of_month", "week_of_year",
    "month", "is_weekend", "is_month_start", "is_month_end",
    "record_count"
]

TARGET_COLUMN = "total_cost_usd"

# Model training
MIN_ROWS_FOR_TRAINING = 45      # skip groups with fewer rows
TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15              # remaining 15% = test
LGBM_PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "n_estimators": 500,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 5,
    "early_stopping_rounds": 20,
    "verbose": -1
}

MODEL_REGISTRY_PATH = "attribution/model_registry"
os.makedirs(MODEL_REGISTRY_PATH, exist_ok=True)
