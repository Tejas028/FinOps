import uuid
import random
import datetime
import pandas as pd
from typing import Dict, Any

from .config import (
    NEGATIVE_COST_RATE,
    DUPLICATE_RATE,
    BACKDATED_RATE,
    NULL_REGION_RATE,
    NULL_RESOURCE_RATE
)

def inject_edge_cases(df: pd.DataFrame, rng) -> pd.DataFrame:
    """Takes a Pandas DataFrame representing a chunk and applies edge cases."""
    if df.empty:
        return df
        
    records = df.to_dict('records')
    new_records = []
    
    for r in records:
        # Negative Costs
        if rng.random() < NEGATIVE_COST_RATE:
            r['cost_usd'] = -(abs(r['cost_usd']) * rng.uniform(0.1, 1.0))
            r['original_cost'] = r['cost_usd'] / r['exchange_rate']
            r['notes'] = "Billing adjustment"
            if "credit_type" not in r['tags']:
                r['tags']["credit_type"] = str(rng.choice(["sustained_use", "committed_use", "support_refund"]))

        # Null Region
        if rng.random() < NULL_REGION_RATE and r.get('service') in ["BigQuery", "Pub/Sub", "Lambda", "CloudFront", "Azure Monitor"]:
            r['region'] = None
            r['tags']["scope"] = "global"

        # Null Resource
        if rng.random() < NULL_RESOURCE_RATE:
            r['resource_id'] = None
            if not r.get('notes'):
                r['notes'] = "Aggregated billing row — no specific resource"

        # Tag Inconsistency
        if "environment" in r['tags']:
            env_val = rng.choice(["prod", "production", "PROD", "Production", "prd",
                                 "dev", "development", "DEV", "Development",
                                 "staging", "stg", "STG", "Staging",
                                 "test", "testing", "QA", "qa"])
            r['tags']["environment"] = str(env_val)

        # Zero usage non-zero cost
        if rng.random() < 0.02:
            r['tags']["usage_quantity"] = "0.0"
            r['cost_usd'] = abs(r['cost_usd']) if abs(r['cost_usd']) > 0 else 0.5
            r['notes'] = "Minimum fee charged — zero usage units consumed"
            
        r['is_duplicate'] = False
        r['is_backdated'] = False

    # After modifying in place, we iterate again to do inserts (duplicates, backdated)
    final_records = []
    for r in records:
        final_records.append(r)
        
        # Duplicates
        if rng.random() < DUPLICATE_RATE:
            dup = r.copy()
            dup['record_id'] = str(uuid.uuid4())
            dup['is_duplicate'] = True
            # Shift ingested_at
            ing_dt = datetime.datetime.fromisoformat(dup['ingested_at'].replace('Z', '+00:00'))
            ing_dt += datetime.timedelta(hours=rng.uniform(2, 6))
            dup['ingested_at'] = ing_dt.isoformat()
            final_records.append(dup)

        # Backdated
        if rng.random() < BACKDATED_RATE:
            # wait, backdated means modifying an existing record or creating a new one?
            # "Apply to BACKDATED_RATE fraction of records" -> modify existing
            r['is_backdated'] = True
            ing_dt = datetime.datetime.fromisoformat(r['ingested_at'].replace('Z', '+00:00'))
            new_usage_date = (ing_dt - datetime.timedelta(days=int(rng.integers(3, 8)))).date()
            r['usage_date'] = new_usage_date.isoformat()
            r['notes'] = "Azure late posting — cost allocation retroactively"

    # Final currency and tags pass to ensure dict serialization if needed
    return pd.DataFrame(final_records)
