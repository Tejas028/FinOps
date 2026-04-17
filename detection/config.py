# ─── Z-Score Detector ────────────────────────────────────────
ZSCORE_THRESHOLD_LOW      = 2.0
ZSCORE_THRESHOLD_MEDIUM   = 2.5
ZSCORE_THRESHOLD_HIGH     = 3.0
ZSCORE_THRESHOLD_CRITICAL = 4.0
ZSCORE_LOOKBACK_DAYS      = 30

# ─── IsolationForest Detector ────────────────────────────────
IFOREST_N_ESTIMATORS      = 200
IFOREST_CONTAMINATION     = 0.08
IFOREST_MAX_SAMPLES       = "auto"
IFOREST_RANDOM_STATE      = 42
IFOREST_FEATURE_COLS = [
    "rolling_mean_7d", "rolling_std_7d",
    "rolling_mean_30d", "rolling_std_30d",
    "pct_change_1d", "pct_change_7d",
    "lag_1d", "lag_7d", "lag_30d",
    "day_of_week", "is_month_end", "is_weekend"
]

# ─── LSTM Autoencoder ────────────────────────────────────────
LSTM_SEQUENCE_LENGTH      = 30
# LOCAL DEV — override for Colab/GPU training: increase to 64 on Colab
LSTM_HIDDEN_UNITS         = 32
LSTM_DROPOUT_RATE         = 0.2
LSTM_BATCH_SIZE           = 32
# LOCAL DEV — override for Colab/GPU training: increase to 200 on Colab
LSTM_MAX_EPOCHS           = 50
LSTM_EARLY_STOPPING_PATIENCE = 10
LSTM_LEARNING_RATE        = 0.001
LSTM_TRAIN_RATIO          = 0.70
LSTM_VAL_RATIO            = 0.15
LSTM_TEST_RATIO           = 0.15
LSTM_MC_DROPOUT_SAMPLES   = 10
LSTM_RECONSTRUCTION_THRESHOLD_PERCENTILE = 95
LSTM_FEATURE_COLS = [
    "rolling_mean_7d", "rolling_std_7d", "rolling_mean_30d",
    "pct_change_1d", "pct_change_7d",
    "lag_1d", "lag_7d", "lag_30d"
]

# ─── Ensemble Scorer ─────────────────────────────────────────
ENSEMBLE_WEIGHT_ZSCORE    = 0.45
ENSEMBLE_WEIGHT_IFOREST   = 0.55
ENSEMBLE_WEIGHT_LSTM      = 0.00

SEVERITY_THRESHOLDS = {
    "low":      0.30,
    "medium":   0.50,
    "high":     0.70,
    "critical": 0.90
}

# ─── Model Registry ──────────────────────────────────────────
MODEL_REGISTRY_PATH       = "detection/model_registry"

# ─── Data ────────────────────────────────────────────────────
MIN_ROWS_FOR_LSTM_TRAINING = 90
MIN_ROWS_FOR_IFOREST       = 30
