import os
import glob
import pandas as pd
from typing import List, Optional
from datetime import date
from shared.schemas.billing import BillingRecord

def read_parquet_records(
    path: str,
    cloud_provider: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: Optional[int] = None
) -> List[BillingRecord]:
    """
    Read parquet files from synthetic_data/output/{cloud_provider}/*.parquet
    - If cloud_provider is None, reads all three clouds
    - Filters by date range if provided
    - CRITICAL: tags column is a JSON string → must be passed as-is to BillingRecord
      (BillingRecord.tags is typed as str, not dict)
    - Returns List[BillingRecord]
    """
    all_files = []
    
    if cloud_provider:
        search_path = os.path.join(path, cloud_provider, "*.parquet")
        all_files.extend(glob.glob(search_path))
    else:
        # Check combined output or read each cloud provider
        combined_path = os.path.join(path, "combined", "all_clouds_billing.parquet")
        if os.path.exists(combined_path):
            all_files.append(combined_path)
        else:
            for cp in ["aws", "azure", "gcp"]:
                search_path = os.path.join(path, cp, "*.parquet")
                all_files.extend(glob.glob(search_path))
                
    if not all_files:
        import logging
        logging.warning(f"No parquet files found in path: {path}")
        return []
        
    dfs = []
    for f in all_files:
        try:
            df = pd.read_parquet(f)
            dfs.append(df)
        except Exception as e:
            import logging
            logging.error(f"Error reading {f}: {e}")
            
    if not dfs:
        return []
        
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Filter by date if needed
    if start_date:
        combined_df = combined_df[pd.to_datetime(combined_df['usage_date']).dt.date >= start_date]
    if end_date:
        combined_df = combined_df[pd.to_datetime(combined_df['usage_date']).dt.date <= end_date]
        
    if limit is not None:
        combined_df = combined_df.head(limit)
        
    # tags logic: PyArrow handles reading string from parquet, so we just convert dict to Pydantic objects.
    # To conform with Pydantic JSON string typing for `tags`:
    records = []
    
    # Pre-clean NaN and empty strings
    combined_df = combined_df.replace({pd.NA: None, float('nan'): None, '': None})
    
    for r in combined_df.to_dict(orient="records"):
        # `tags` is inherently read as string since it was dumped to JSON string during generation.
        # So we pass it as-is.
        records.append(BillingRecord(**r))
        
    return records
