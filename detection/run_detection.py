"""Anomaly Detection CLI entry point."""
import argparse
import sys
from datetime import date

from storage.db import DatabaseManager
from detection.engine import DetectionEngine


def main():
    parser = argparse.ArgumentParser(description="Anomaly Detection Engine")
    parser.add_argument("--cloud", type=str, default="all",
                        choices=["aws", "azure", "gcp", "all"])
    parser.add_argument("--start", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--mode", type=str, default="train_predict",
                        choices=["train", "predict", "train_predict"])
    parser.add_argument("--force-retrain", action="store_true")
    args = parser.parse_args()

    DatabaseManager.initialize()

    engine = DetectionEngine(mode=args.mode)
    cloud = args.cloud if args.cloud != "all" else None

    results = engine.run(
        start_date=date.fromisoformat(args.start),
        end_date=date.fromisoformat(args.end),
        cloud_provider=cloud,
        force_retrain=args.force_retrain,
    )

    print(f"\nTotal anomalies detected: {len(results)}")

    DatabaseManager.close()


if __name__ == "__main__":
    main()
