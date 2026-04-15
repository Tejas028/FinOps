import argparse
from datetime import datetime
from storage.client import StorageClient
from forecasting.engine import ForecastingEngine
from forecasting import config

def parse_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def main():
    parser = argparse.ArgumentParser(description="Multi-model spend forecasting engine")
    parser.add_argument("--cloud", type=str, default="all", help="aws | azure | gcp | all")
    parser.add_argument("--start", type=parse_date, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", type=parse_date, required=True, help="YYYY-MM-DD")
    parser.add_argument("--force-retrain", action="store_true", help="Ignore saved models and retrain")
    parser.add_argument("--horizons", type=str, default="7,14,30,90", help="Comma-separated list of horizons")
    
    args = parser.parse_args()
    
    # Override horizons if provided
    try:
        custom_horizons = [int(x.strip()) for x in args.horizons.split(",") if x.strip()]
        if custom_horizons:
            config.FORECAST_HORIZONS = custom_horizons
    except Exception as e:
        print(f"Error parsing horizons: {e}")
        return

    # Initialize Engine
    storage_client = StorageClient()
    engine = ForecastingEngine(storage_client=storage_client, force_retrain=args.force_retrain)
    
    # Run
    try:
        engine.run(
            cloud_provider=args.cloud,
            start_date=args.start,
            end_date=args.end
        )
    except Exception as e:
        print(f"Engine execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
