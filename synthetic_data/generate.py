import os
import numpy as np
import uuid
import json
import click
import datetime
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from rich.console import Console
from rich.table import Table

from generator.config import (
    DATE_RANGE_START, DATE_RANGE_END, RANDOM_SEED,
    AWS_RECORDS_PER_DAY, AZURE_RECORDS_PER_DAY, GCP_RECORDS_PER_DAY,
    CURRENCY_DIST
)
from generator.aws_generator import AWS_SERVICES, AWS_REGIONS, AWS_ACCOUNT_IDS
from generator.azure_generator import AZURE_SERVICES, AZURE_REGIONS, AZURE_SUBSCRIPTION_IDS
from generator.gcp_generator import GCP_SERVICES, GCP_REGIONS, GCP_GLOBAL_SERVICES, GCP_PROJECT_IDS
from generator.base_generator import get_baseline_multiplier, get_region_multiplier, get_rng
from generator.anomaly_injector import build_anomaly_schedule
from generator.edge_case_injector import inject_edge_cases
from generator.schema import BillingRecord

DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output"

console = Console()

# Fixed base exchange rates roughly
BASE_EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.25,
    "CNY": 0.14,
    "INR": 0.012
}

def generate_month_chunk(
    start_d: datetime.date, 
    end_d: datetime.date, 
    schedule: dict, 
    clouds: list, 
    apply_anomalies: bool,
    apply_edge_cases: bool,
    rng
) -> pd.DataFrame:
    
    records = []
    
    current_d = start_d
    while current_d <= end_d:
        date_str = current_d.isoformat()
        base_mult = get_baseline_multiplier(current_d, rng)
        
        # We process daily currency fluctuations for CNY and INR
        daily_rates = BASE_EXCHANGE_RATES.copy()
        daily_rates["CNY"] *= rng.uniform(0.97, 1.03) # ±3% daily fluctuation
        daily_rates["INR"] *= rng.uniform(0.97, 1.03)
        
        # Tags pool
        teams = ["platform","data-eng","ml-ops","backend","frontend","security","finops","devops"]
        projects = ["apollo","orion","zeus","athena","titan","nova","phoenix","nexus"]
        owners = ["alice@company.com","bob@company.com","carol@company.com","dave@company.com"]
        
        for cloud in clouds:
            num_records = 0
            services = {}
            regions = []
            accounts = []
            
            if cloud == 'aws':
                num_records = AWS_RECORDS_PER_DAY
                services = AWS_SERVICES
                regions = AWS_REGIONS
                accounts = AWS_ACCOUNT_IDS
            elif cloud == 'azure':
                num_records = AZURE_RECORDS_PER_DAY
                services = AZURE_SERVICES
                regions = AZURE_REGIONS
                accounts = AZURE_SUBSCRIPTION_IDS
            elif cloud == 'gcp':
                num_records = GCP_RECORDS_PER_DAY
                services = GCP_SERVICES
                regions = GCP_REGIONS
                accounts = GCP_PROJECT_IDS
                
            svc_list = list(services.keys())
            
            for _ in range(num_records):
                svc = rng.choice(svc_list)
                reg = rng.choice(regions)
                
                # GCP Global services 30% rule
                if cloud == 'gcp' and svc in GCP_GLOBAL_SERVICES:
                    if rng.random() < 0.3:
                        reg = None
                
                acct = rng.choice(accounts)
                base_cost, std_dev = services[svc]
                
                # Apportion base cost to records (approximate)
                cost = (base_cost / (num_records / len(svc_list))) + rng.normal(0, std_dev / (num_records / len(svc_list)))
                cost = max(1.0, cost)

                cost_usd = cost * base_mult * get_region_multiplier(reg)
                
                is_anomaly = False
                anomaly_type = None
                severity = None
                
                if apply_anomalies:
                    # O(1) Anomaly lookup
                    day_schedule = schedule.get(date_str, {})
                    entry = day_schedule.get((cloud, svc, reg))
                    if entry:
                        cost_usd *= entry["multiplier"]
                        is_anomaly = entry.get("is_anomaly", True)
                        anomaly_type = entry.get("anomaly_type")
                        severity = entry.get("severity")
                
                # Currency
                orig_currency = "USD"
                
                # Distribute currency
                r_num = rng.random()
                cumulative = 0.0
                for c_name, c_prob in CURRENCY_DIST.items():
                    cumulative += c_prob
                    if r_num <= cumulative:
                        orig_currency = c_name
                        break
                        
                # Azure restriction
                if cloud == 'azure' and rng.random() < 0.4:
                    orig_currency = rng.choice(["EUR", "GBP"])
                
                exch_rate = daily_rates[orig_currency]
                original_cost = cost_usd / exch_rate
                
                tags = {
                    "team": rng.choice(teams),
                    "project": rng.choice(projects),
                    "owner": rng.choice(owners)
                }
                if rng.random() < 0.5:
                    tags["cost_center"] = rng.choice(["cc-1001","cc-1002","cc-1003","cc-2001","cc-2002"])
                if rng.random() < 0.5:
                    tags["tier"] = rng.choice(["standard","premium","enterprise"])
                    
                # Tag explosion overrides
                if apply_anomalies and anomaly_type == "tag_explosion":
                    tags = {f"spam_key_{i}": f"spam_val_{rng.integers(100, 999)}" for i in range(rng.integers(40, 80))}

                record_dt = datetime.datetime.fromisoformat(date_str) + datetime.timedelta(
                    hours=int(rng.integers(0, 23)),
                    minutes=int(rng.integers(0, 59))
                )
                    
                r = {
                    "record_id": str(uuid.uuid4()),
                    "cloud_provider": cloud,
                    "account_id": str(acct),
                    "service": str(svc),
                    "region": reg,
                    "resource_id": f"arn:uuid:{uuid.uuid4()}" if reg else None,
                    "usage_date": date_str,
                    "cost_usd": float(cost_usd),
                    "original_cost": float(original_cost),
                    "original_currency": orig_currency,
                    "exchange_rate": float(exch_rate),
                    "tags": tags,
                    "ingested_at": (record_dt + datetime.timedelta(hours=int(rng.integers(2, 6)))).isoformat() + "Z",
                    "is_anomaly": is_anomaly,
                    "anomaly_type": anomaly_type,
                    "anomaly_severity": severity,
                    "is_duplicate": False,
                    "is_backdated": False,
                    "notes": None
                }
                
                records.append(r)
                
        current_d += datetime.timedelta(days=1)
        
    df = pd.DataFrame(records)
    if apply_edge_cases and not df.empty:
        df = inject_edge_cases(df, rng)
        
    return df


@click.command()
@click.option('--cloud', default='all', type=click.Choice(['aws', 'azure', 'gcp', 'all']), help='Cloud provider to generate for.')
@click.option('--start', default=DATE_RANGE_START, help='Start date (YYYY-MM-DD)')
@click.option('--end', default=DATE_RANGE_END, help='End date (YYYY-MM-DD)')
@click.option('--seed', default=RANDOM_SEED, type=int, help='Random seed')
@click.option('--no-anomalies', is_flag=True, help='Skip anomaly injection')
@click.option('--no-edge-cases', is_flag=True, help='Skip edge case injection')
@click.option('--output-dir', default=str(DEFAULT_OUTPUT_DIR), type=click.Path(), help='Output directory')
@click.option('--format', 'out_format', default='both', type=click.Choice(['csv', 'parquet', 'both']), help='Output format')
def main(cloud, start, end, seed, no_anomalies, no_edge_cases, output_dir, out_format):
    console.print("[bold green]Starting Synthetic Dataset Generation...[/bold green]")
    rng = np.random.default_rng(seed)
    
    start_d = datetime.date.fromisoformat(start)
    end_d = datetime.date.fromisoformat(end)
    out_path = Path(output_dir)
    
    clouds_to_gen = ['aws', 'azure', 'gcp'] if cloud == 'all' else [cloud]
    
    for c in clouds_to_gen:
        (out_path / c).mkdir(parents=True, exist_ok=True)
    (out_path / 'combined').mkdir(parents=True, exist_ok=True)
    
    schedule = {}
    manifest = []
    
    if not no_anomalies:
        console.print("Pre-computing anomaly schedule... Phase 1")
        # Ensure base generator seed is synced
        import generator.base_generator as bg
        bg.RANDOM_SEED = seed # For get_rng inner working if used
        schedule, manifest = build_anomaly_schedule()
        
    # Month by month generation chunked
    current_chunk_start = start_d
    
    # Trackers for summary
    stats = {c: {"records": 0, "anomalies": 0, "edges": 0} for c in clouds_to_gen}
    
    # Create parquet writers
    pq_writers_labeled = {}
    pq_combined_writer = None
    csv_files = {}
    
    first_chunk = True
    
    while current_chunk_start <= end_d:
        import calendar
        _, last_day = calendar.monthrange(current_chunk_start.year, current_chunk_start.month)
        current_chunk_end = datetime.date(current_chunk_start.year, current_chunk_start.month, last_day)
        if current_chunk_end > end_d:
            current_chunk_end = end_d
            
        console.print(f"Generating chunk: {current_chunk_start} to {current_chunk_end}")
        
        df_chunk = generate_month_chunk(
            current_chunk_start, current_chunk_end, schedule, clouds_to_gen,
            not no_anomalies, not no_edge_cases, rng
        )
        
        if df_chunk.empty:
            current_chunk_start = current_chunk_end + datetime.timedelta(days=1)
            continue
            
        # Ensure consistent types for Parquet serialization
        for col in ['anomaly_type', 'anomaly_severity', 'notes', 'region', 'resource_id']:
            df_chunk[col] = df_chunk[col].fillna('').astype(str)
        
        # Tags are arbitrary (especially tag_explosion), so store as JSON strings 
        # to ensure a stable schema in Parquet.
        df_chunk['tags'] = df_chunk['tags'].apply(json.dumps)
        
        for c in clouds_to_gen:
            c_df = df_chunk[df_chunk['cloud_provider'] == c].copy()
            if c_df.empty: continue
            
            stats[c]["records"] += len(c_df)
            stats[c]["anomalies"] += len(c_df[c_df['is_anomaly'] == True])
            stats[c]["edges"] += len(c_df[(c_df['is_duplicate'] == True) | (c_df['is_backdated'] == True) | (c_df['cost_usd'] < 0)])
            
            labeled_path = out_path / c / f"{c}_billing_labeled.parquet"
            raw_path = out_path / c / f"{c}_billing_raw.csv"
            
            table = pa.Table.from_pandas(c_df)
            
            if out_format in ['parquet', 'both']:
                if c not in pq_writers_labeled:
                    pq_writers_labeled[c] = pq.ParquetWriter(labeled_path, table.schema)
                pq_writers_labeled[c].write_table(table)
                
            if out_format in ['csv', 'both']:
                # The raw CSV intentional omit tracking info
                raw_df = c_df.drop(columns=['is_anomaly', 'anomaly_type', 'anomaly_severity', 'is_duplicate', 'is_backdated'])
                raw_df.to_csv(raw_path, mode='a', header=first_chunk, index=False)
                
        # Combined
        if out_format in ['parquet', 'both']:
            combined_table = pa.Table.from_pandas(df_chunk.sort_values(by='usage_date'))
            if not pq_combined_writer:
                pq_combined_writer = pq.ParquetWriter(out_path / 'combined' / "all_clouds_billing.parquet", combined_table.schema)
            pq_combined_writer.write_table(combined_table)
            
        first_chunk = False
        current_chunk_start = current_chunk_end + datetime.timedelta(days=1)

    for w in pq_writers_labeled.values():
        w.close()
    if pq_combined_writer:
        pq_combined_writer.close()
        
    if not no_anomalies:
        manifest_data = {
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "date_range": {"start": start, "end": end},
            "total_records": sum([v["records"] for v in stats.values()]),
            "total_anomaly_records": sum([v["anomalies"] for v in stats.values()]),
            "anomaly_rate_actual": sum([v["anomalies"] for v in stats.values()]) / max(1, sum([v["records"] for v in stats.values()])),
            "anomalies": manifest
        }
        with open(out_path / 'combined' / 'anomaly_manifest.json', 'w') as f:
            json.dump(manifest_data, f, indent=2)

    table = Table(title="Generation Summary")
    table.add_column("Cloud", justify="left")
    table.add_column("Records", justify="right")
    table.add_column("Anomaly Records", justify="right")
    table.add_column("Edge Cases", justify="right")
    table.add_column("Output", justify="left")
    
    for c in clouds_to_gen:
        table.add_row(
            c.upper(),
            f"{stats[c]['records']:,}",
            f"{stats[c]['anomalies']:,}",
            f"{stats[c]['edges']:,}",
            f"{out_path / c}"
        )
        
    console.print(table)


if __name__ == '__main__':
    main()
