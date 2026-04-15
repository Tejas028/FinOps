"""Feature Engineering CLI entrypoint."""
import argparse
import sys
from datetime import date, timedelta

from storage.db import DatabaseManager
from features.pipeline import FeatureEngineeringPipeline
from features.repository import FeatureRepository


def main():
    parser = argparse.ArgumentParser(description="Feature Engineering Pipeline")
    parser.add_argument("--start", type=str, default="2023-01-01",
                        help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=None,
                        help="End date (YYYY-MM-DD, default: yesterday)")
    parser.add_argument("--cloud", type=str, default="all",
                        choices=["aws", "azure", "gcp", "all"],
                        help="Cloud provider filter")
    parser.add_argument("--incremental", action="store_true",
                        help="Run for last 7 days only")
    args = parser.parse_args()

    # Initialize DB
    DatabaseManager.initialize()

    pipeline = FeatureEngineeringPipeline()

    if args.incremental:
        result = pipeline.run_incremental(days_back=7)
    else:
        start_date = date.fromisoformat(args.start)
        end_date = (date.fromisoformat(args.end) if args.end
                    else date.today() - timedelta(days=1))
        cloud = args.cloud if args.cloud != "all" else None
        result = pipeline.run(
            start_date=start_date,
            end_date=end_date,
            cloud_provider=cloud
        )

    # Print summary table
    print("\nFeature Engineering Complete")
    print("+---------------------------------------+")
    print(f"| Groups Processed  | {result.groups_processed:<18}|")
    print(f"| Features Written  | {result.features_written:<18}|")
    print(f"| Duration          | {result.duration_seconds:.1f}s{' ' * (16 - len(f'{result.duration_seconds:.1f}s'))}|")
    print(f"| Errors            | {len(result.errors):<18}|")
    print("+---------------------------------------+")

    if result.errors:
        print("\nErrors:")
        for e in result.errors[:10]:
            print(f"  - {e}")

    # Show top 5 z-score anomalies
    try:
        repo = FeatureRepository()
        top_z = repo.get_features(
            start_date=result.start_date,
            end_date=result.end_date,
            min_z_score=2.0
        )
        # Sort by absolute z-score descending
        top_z.sort(key=lambda r: abs(r.get("z_score_30d") or 0), reverse=True)
        top_5 = top_z[:5]

        if top_5:
            print("\nTop 5 Z-Score Anomalies Detected:")
            print(f"{'Date':<12}| {'Cloud':<8}| {'Service':<16}| {'Account':<16}| {'Z-Score':<10}")
            print("-" * 66)
            for row in top_5:
                print(
                    f"{str(row['feature_date']):<12}| "
                    f"{row['cloud_provider']:<8}| "
                    f"{row['service_category']:<16}| "
                    f"{row['account_id']:<16}| "
                    f"{row.get('z_score_30d', 0):<10.2f}"
                )
        else:
            print("\nNo z-score anomalies > 2.0 detected in the range.")
    except Exception as e:
        print(f"\nWarning: Could not query top z-scores: {e}")

    DatabaseManager.close()

    if result.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
