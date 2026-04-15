from ingestion.adapters.synthetic_adapter import SyntheticAdapter
from normalization.pipeline import NormalizationPipeline
from storage.client import StorageClient
from storage.db import DatabaseManager
from datetime import date
import time

def run_full_pipeline(
    start_date: date,
    end_date: date,
    cloud_provider: str = "aws"
) -> dict:
    
    start_ts = time.time()
    
    DatabaseManager.initialize()
    
    records = SyntheticAdapter().fetch(start_date, end_date, cloud_provider)
    ingested_count = len(records)
    
    norm_result = NormalizationPipeline().normalize(records)
    normalized_count = norm_result.output_count
    
    client = StorageClient()
    upsert_result = client.upsert_records(norm_result.records)
    
    aggs_written = client.refresh_daily_aggregates(start_date, end_date)
    
    total_time = time.time() - start_ts
    
    client.log_ingestion_run(
        cloud_provider=cloud_provider,
        inserted=upsert_result.inserted,
        skipped=upsert_result.skipped,
        date_start=start_date,
        date_end=end_date,
        duration_seconds=total_time,
        status="success"
    )
    
    return {
        "ingested": ingested_count,
        "normalized": normalized_count,
        "inserted": upsert_result.inserted,
        "skipped": upsert_result.skipped,
        "aggregates": aggs_written,
        "duration": total_time
    }

if __name__ == "__main__":
    result = run_full_pipeline(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        cloud_provider="aws"
    )
    print(result)
