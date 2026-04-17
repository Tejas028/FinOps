import click
import logging
import sys
from datetime import date, datetime
import time
from typing import List

from ingestion.adapters.synthetic_adapter import SyntheticAdapter
from normalization.pipeline import NormalizationPipeline
from storage.client import StorageClient
from storage.db import DatabaseManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_single_cloud(
    cloud_provider: str,
    start_date: date,
    end_date: date,
    client: StorageClient,
    norm_pipeline: NormalizationPipeline,
    adapter: SyntheticAdapter
) -> dict:
    """Run the 4-step pipeline for a specific cloud provider."""
    logger.info(f"Starting pipeline for {cloud_provider.upper()} ({start_date} to {end_date})")
    
    t0 = time.time()
    
    # 1. Fetch
    records = adapter.fetch_by_cloud(cloud_provider, start_date, end_date)
    ingested_count = len(records)
    logger.info(f"[{cloud_provider}] Fetched {ingested_count} records")
    
    if ingested_count == 0:
        return {"cloud": cloud_provider, "status": "skipped", "reason": "no data"}

    # 2. Normalize
    norm_result = norm_pipeline.normalize(records)
    logger.info(f"[{cloud_provider}] Normalized {norm_result.output_count} records")
    
    # 3. Upsert to billing_records
    upsert_result = client.upsert_records(norm_result.records)
    logger.info(f"[{cloud_provider}] Inserted {upsert_result.inserted}, Skipped {upsert_result.skipped}")
    
    # 4. Refresh daily_aggregates
    aggs_written = client.refresh_daily_aggregates(start_date, end_date)
    logger.info(f"[{cloud_provider}] Refreshed {aggs_written} daily aggregates")
    
    duration = time.time() - t0
    
    # Log run
    client.log_ingestion_run(
        cloud_provider=cloud_provider,
        inserted=upsert_result.inserted,
        skipped=upsert_result.skipped,
        date_start=start_date,
        date_end=end_date,
        duration_seconds=duration,
        status="success"
    )
    
    return {
        "cloud": cloud_provider,
        "ingested": ingested_count,
        "inserted": upsert_result.inserted,
        "skipped": upsert_result.skipped,
        "aggregates": aggs_written,
        "duration": duration
    }

@click.command()
@click.option('--mode', default='all', type=click.Choice(['aws', 'azure', 'gcp', 'all']), help='Cloud provider to process.')
@click.option('--start', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end', required=True, help='End date (YYYY-MM-DD)')
def main(mode, start, end):
    """
    Storage Runner CLI: Moves data from Ingestion -> Normalization -> Storage -> Aggregation.
    This bridge script ensures the cloud database is synced for the specified date range.
    """
    DatabaseManager.initialize()
    
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    
    client = StorageClient()
    norm_pipeline = NormalizationPipeline()
    adapter = SyntheticAdapter()
    
    clouds = ['aws', 'azure', 'gcp'] if mode == 'all' else [mode]
    
    all_results = []
    
    for cloud in clouds:
        try:
            res = run_single_cloud(cloud, start_date, end_date, client, norm_pipeline, adapter)
            all_results.append(res)
        except Exception as e:
            logger.error(f"Failed to process {cloud}: {e}")
            all_results.append({"cloud": cloud, "status": "error", "error": str(e)})

    # Print summary
    print("\n" + "="*50)
    print(f"PIPELINE SUMMARY ({start} to {end})")
    print("="*50)
    for r in all_results:
        if "error" in r:
            print(f"{r['cloud'].upper():<6} | ERROR: {r['error']}")
        elif r.get("status") == "skipped":
            print(f"{r['cloud'].upper():<6} | SKIPPED (No data)")
        else:
            print(f"{r['cloud'].upper():<6} | Ingested: {r['ingested']:,} | Store: {r['inserted']:,} | Aggs: {r['aggregates']:,}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
