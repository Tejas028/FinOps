import os
import json
import logging
import numpy as np
import pandas as pd
import joblib
from typing import List, Dict, Optional

from detection.detectors.base_detector import BaseDetector, DetectorResult
from detection import config

logger = logging.getLogger(__name__)

# Suppress TF warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"


def _build_lstm_autoencoder(seq_len: int, n_features: int):
    """Build LSTM encoder-decoder autoencoder."""
    import tensorflow as tf
    from tensorflow import keras

    model = keras.Sequential([
        # Encoder
        keras.layers.LSTM(
            config.LSTM_HIDDEN_UNITS,
            input_shape=(seq_len, n_features),
            return_sequences=False,
            dropout=config.LSTM_DROPOUT_RATE,
        ),
        # Decoder
        keras.layers.RepeatVector(seq_len),
        keras.layers.LSTM(
            config.LSTM_HIDDEN_UNITS,
            return_sequences=True,
            dropout=config.LSTM_DROPOUT_RATE,
        ),
        keras.layers.TimeDistributed(keras.layers.Dense(n_features)),
    ])
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=config.LSTM_LEARNING_RATE),
        loss="mse",
    )
    return model


class LSTMDetector(BaseDetector):
    """LSTM Autoencoder detector with MC Dropout inference."""

    def __init__(self):
        self.models: Dict[str, object] = {}  # key -> keras model
        self.scalers: Dict[str, object] = {}  # key -> MinMaxScaler
        self.thresholds: Dict[str, float] = {}
        self.metadata: Dict[str, dict] = {}

    def fit(self, df: pd.DataFrame) -> None:
        import tensorflow as tf
        from sklearn.preprocessing import MinMaxScaler

        groups = df.groupby(["cloud_provider", "service_category"])
        summaries = []

        for (cloud, service), group_df in groups:
            key = f"{cloud}_{service}"
            group_df = group_df.sort_values("feature_date" if "feature_date" in group_df.columns else "agg_date")

            if len(group_df) < config.MIN_ROWS_FOR_LSTM_TRAINING:
                logger.info(f"Skipping LSTM for {key}: only {len(group_df)} rows (need {config.MIN_ROWS_FOR_LSTM_TRAINING})")
                continue

            # Extract features
            feature_cols = [c for c in config.LSTM_FEATURE_COLS if c in group_df.columns]
            if len(feature_cols) < 3:
                continue

            data = group_df[feature_cols].fillna(0).values

            # Time-ordered split
            n = len(data)
            train_end = int(n * config.LSTM_TRAIN_RATIO)
            val_end = train_end + int(n * config.LSTM_VAL_RATIO)

            train_data = data[:train_end]
            val_data = data[train_end:val_end]
            test_data = data[val_end:]

            if len(train_data) < config.LSTM_SEQUENCE_LENGTH + 1:
                continue

            # Scale
            scaler = MinMaxScaler()
            train_scaled = scaler.fit_transform(train_data)
            val_scaled = scaler.transform(val_data) if len(val_data) > 0 else np.array([])
            test_scaled = scaler.transform(test_data) if len(test_data) > 0 else np.array([])

            # Create sequences
            X_train = self._create_sequences(train_scaled)
            X_val = self._create_sequences(val_scaled) if len(val_scaled) > config.LSTM_SEQUENCE_LENGTH else np.array([])
            X_test = self._create_sequences(test_scaled) if len(test_scaled) > config.LSTM_SEQUENCE_LENGTH else np.array([])

            if len(X_train) == 0:
                continue

            n_features = X_train.shape[2]
            model = _build_lstm_autoencoder(config.LSTM_SEQUENCE_LENGTH, n_features)

            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor="val_loss" if len(X_val) > 0 else "loss",
                    patience=config.LSTM_EARLY_STOPPING_PATIENCE,
                    restore_best_weights=True,
                    min_delta=1e-4,
                ),
            ]

            fit_kwargs = {
                "x": X_train, "y": X_train,
                "epochs": config.LSTM_MAX_EPOCHS,
                "batch_size": config.LSTM_BATCH_SIZE,
                "callbacks": callbacks,
                "verbose": 0,
            }
            if len(X_val) > 0:
                fit_kwargs["validation_data"] = (X_val, X_val)

            history = model.fit(**fit_kwargs)

            # Compute threshold on test set
            if len(X_test) > 0:
                reconstructed = model.predict(X_test, verbose=0)
                test_errors = np.mean(np.square(X_test - reconstructed), axis=(1, 2))
                threshold = float(np.percentile(test_errors, config.LSTM_RECONSTRUCTION_THRESHOLD_PERCENTILE))
            else:
                # Fallback: use training errors
                reconstructed = model.predict(X_train, verbose=0)
                train_errors = np.mean(np.square(X_train - reconstructed), axis=(1, 2))
                threshold = float(np.percentile(train_errors, config.LSTM_RECONSTRUCTION_THRESHOLD_PERCENTILE))

            best_epoch = len(history.history["loss"])
            if "val_loss" in history.history:
                best_val = min(history.history["val_loss"])
            else:
                best_val = min(history.history["loss"])

            self.models[key] = model
            self.scalers[key] = scaler
            self.thresholds[key] = threshold
            self.metadata[key] = {
                "cloud": cloud, "service": service,
                "train_size": len(X_train), "val_size": len(X_val),
                "test_size": len(X_test), "best_epoch": best_epoch,
                "final_val_loss": float(best_val),
                "test_error_p95_threshold": threshold,
                "feature_cols": feature_cols,
            }

            summaries.append(self.metadata[key])
            logger.info(f"LSTM {key}: epoch={best_epoch}, val_loss={best_val:.6f}, threshold={threshold:.6f}")

        if summaries:
            print(f"\nLSTM Training Summary ({len(summaries)} models):")
            print(f"{'Key':<30} {'Epoch':<8} {'Val Loss':<12} {'Threshold':<12}")
            print("-" * 62)
            for m in summaries:
                k = f"{m['cloud']}_{m['service']}"
                print(f"{k:<30} {m['best_epoch']:<8} {m['final_val_loss']:<12.6f} {m['test_error_p95_threshold']:<12.6f}")

    def predict(self, df: pd.DataFrame) -> List[DetectorResult]:
        results = []
        groups = df.groupby(["cloud_provider", "service_category"])

        for (cloud, service), group_df in groups:
            key = f"{cloud}_{service}"
            group_df = group_df.sort_values("feature_date" if "feature_date" in group_df.columns else "agg_date")

            if key not in self.models:
                for _, row in group_df.iterrows():
                    results.append(self._make_result(row, 0.0, None))
                continue

            model = self.models[key]
            scaler = self.scalers[key]
            threshold = self.thresholds[key]
            meta = self.metadata.get(key, {})
            feature_cols = meta.get("feature_cols", config.LSTM_FEATURE_COLS)
            feature_cols = [c for c in feature_cols if c in group_df.columns]

            data = group_df[feature_cols].fillna(0).values
            scaled = scaler.transform(data)

            # Step 1: Collect all possible sequences into a batch
            sequences = []
            valid_indices = []

            for idx in range(len(group_df)):
                if idx >= config.LSTM_SEQUENCE_LENGTH - 1:
                    seq = scaled[idx - config.LSTM_SEQUENCE_LENGTH + 1 : idx + 1]
                    sequences.append(seq)
                    valid_indices.append(idx)

            if not sequences:
                for _, row in group_df.iterrows():
                    results.append(self._make_result(row, 0.0, None))
                continue

            X_all = np.array(sequences)  # Shape: (num_valid, seq_len, num_features)

            # Step 2: Batch MC Dropout Inference
            # We run the entire batch through the model 10 times with training=True
            mc_reconstruction_errors = []

            # Sub-batching to avoid massive memory spikes if X_all is huge
            inference_batch_size = 128
            
            for _ in range(config.LSTM_MC_DROPOUT_SAMPLES):
                batch_errors = []
                for i in range(0, len(X_all), inference_batch_size):
                    batch_seq = X_all[i : i + inference_batch_size]
                    # Direct call to model with training=True keeps dropout active
                    recon = model(batch_seq, training=True).numpy()
                    # Calculate MSE for this sub-batch: mean over (seq_len, features)
                    mse = np.mean(np.square(batch_seq - recon), axis=(1, 2))
                    batch_errors.append(mse)
                
                mc_reconstruction_errors.append(np.concatenate(batch_errors))

            mc_reconstruction_errors = np.stack(mc_reconstruction_errors) # Shape: (samples, num_valid)
            
            # Step 3: Compute statistics across MC samples
            mean_errors = np.mean(mc_reconstruction_errors, axis=0)
            std_errors = np.std(mc_reconstruction_errors, axis=0)

            # Step 4: Build mapped results
            valid_lookup = {idx: i for i, idx in enumerate(valid_indices)}
            
            for idx in range(len(group_df)):
                row = group_df.iloc[idx]
                if idx in valid_lookup:
                    pos = valid_lookup[idx]
                    mean_err = float(mean_errors[pos])
                    std_err = float(std_errors[pos])
                    raw_score = min(1.0, mean_err / threshold) if threshold > 0 else 0.0
                    results.append(self._make_result(row, raw_score, std_err))
                else:
                    results.append(self._make_result(row, 0.0, None))

        return results

    def _make_result(self, row, raw_score: float, std_error: Optional[float]) -> DetectorResult:
        expected = float(row.get("rolling_mean_30d", 0) or 0)
        actual = float(row.get("total_cost_usd", 0) or 0)
        deviation_pct = ((actual - expected) / expected * 100) if expected > 0 else 0.0

        return DetectorResult(
            record_id=str(row.get("record_id", f"{row.get('cloud_provider')}_{row.get('service_category')}_{row.get('account_id')}_{row.get('feature_date', row.get('agg_date'))}")),
            usage_date=row.get("feature_date", row.get("agg_date")),
            cloud_provider=str(row.get("cloud_provider", "")),
            service=str(row.get("service_category", "")),
            account_id=str(row.get("account_id", "")),
            raw_score=raw_score,
            expected_cost=expected,
            actual_cost=actual,
            deviation_pct=deviation_pct,
            detector_name="lstm"
        )

    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        if len(data) < config.LSTM_SEQUENCE_LENGTH:
            return np.array([])
        seqs = []
        for i in range(len(data) - config.LSTM_SEQUENCE_LENGTH + 1):
            seqs.append(data[i:i + config.LSTM_SEQUENCE_LENGTH])
        return np.array(seqs)

    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        for key in self.models:
            self.models[key].save(os.path.join(path, f"lstm_{key}.keras"))
            joblib.dump(self.scalers[key], os.path.join(path, f"lstm_{key}_scaler.pkl"))
            with open(os.path.join(path, f"lstm_{key}_meta.json"), "w") as f:
                meta = self.metadata.get(key, {})
                meta["threshold"] = self.thresholds.get(key, 0.0)
                json.dump(meta, f)

    def load(self, path: str) -> None:
        import tensorflow as tf
        if not os.path.exists(path):
            return
        for fname in os.listdir(path):
            if fname.startswith("lstm_") and fname.endswith(".keras"):
                key = fname.replace("lstm_", "").replace(".keras", "")
                self.models[key] = tf.keras.models.load_model(os.path.join(path, fname))
                scaler_path = os.path.join(path, f"lstm_{key}_scaler.pkl")
                if os.path.exists(scaler_path):
                    self.scalers[key] = joblib.load(scaler_path)
                meta_path = os.path.join(path, f"lstm_{key}_meta.json")
                if os.path.exists(meta_path):
                    with open(meta_path) as f:
                        meta = json.load(f)
                    self.thresholds[key] = meta.get("threshold", 0.0)
                    self.metadata[key] = meta
