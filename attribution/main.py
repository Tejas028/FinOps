import argparse
from datetime import datetime

from attribution.repository import AttributionRepository
from attribution.engine import AttributionEngine

def parse_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def main():
    parser = argparse.ArgumentParser(description="SHAP Cost Attribution Engine")
    parser.add_argument("--start", type=parse_date, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", type=parse_date, required=True, help="YYYY-MM-DD")
    parser.add_argument("--cloud", type=str, default="all", help="aws | azure | gcp | all")
    parser.add_argument("--force-retrain", action="store_true", help="Ignore saved models and retrain")
    
    args = parser.parse_args()
    
    repo = AttributionRepository()
    engine = AttributionEngine(repository=repo)
    
    result = engine.run(
        start_date=args.start,
        end_date=args.end,
        cloud_provider=args.cloud,
        force_retrain=args.force_retrain
    )
    
    print("Execution Results:")
    print(f"Groups processed:     {result.groups_processed}")
    print(f"Groups skipped:       {result.groups_skipped}")
    print(f"Attributions written: {result.attributions_written}")
    print(f"Avg R² score:         {result.avg_r2_score:.4f}")
    print(f"Duration:             {result.duration_seconds:.2f}s")
    print(f"Errors:               {len(result.errors)}")
    
    if result.errors:
        for err in result.errors:
            print(f" - {err}")

if __name__ == "__main__":
    main()
