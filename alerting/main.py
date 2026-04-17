import argparse
from datetime import date
from alerting.engine import AlertingEngine
from storage.db import DatabaseManager

def main():
    parser = argparse.ArgumentParser(description="FinOps Alerting Engine")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--cloud", type=str, default="all", choices=["aws", "azure", "gcp", "all"])
    parser.add_argument("--budget", type=float, default=None, help="Optional monthly budget in USD")
    
    args = parser.parse_args()
    
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)
    
    DatabaseManager.initialize()
    engine = AlertingEngine()
    
    result = engine.run(
        start_date=start_date,
        end_date=end_date,
        cloud_provider=args.cloud if args.cloud != "all" else None,
        monthly_budget_usd=args.budget
    )
    
    print("Alerting Engine Execution Summary:")
    print("-" * 40)
    print(f"Anomaly alerts generated:      {result['anomaly_alerts']}")
    print(f"Spend spike alerts:            {result['spend_spike_alerts']}")
    print(f"Budget alerts:                 {result['budget_alerts']}")
    print(f"Total inserted:                {result['total_inserted']}")
    print(f"Total skipped (dedup):         {result['total_skipped']}")
    print(f"Duration:                      {result['duration_seconds']:.2f}s")
    
    DatabaseManager.close()

if __name__ == "__main__":
    main()
