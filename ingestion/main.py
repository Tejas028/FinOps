import click
import logging
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table

from ingestion.state_manager import StateManager
from ingestion.scheduler import IngestionScheduler
from ingestion.adapters.synthetic_adapter import SyntheticAdapter
from ingestion.adapters.aws_adapter import AWSCURAdapter
from ingestion.adapters.azure_adapter import AzureCostAdapter
from ingestion.adapters.gcp_adapter import GCPBillingAdapter
from shared.utils.date_utils import utc_now

console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

@click.command()
@click.option('--mode', default='synthetic', type=click.Choice(['synthetic', 'aws', 'azure', 'gcp', 'all']), help='Adapter to run.')
@click.option('--start', help='Start date (YYYY-MM-DD)')
@click.option('--end', help='End date (YYYY-MM-DD)')
@click.option('--reset', is_flag=True, help='Reset ingestion state before running')
@click.option('--schedule', is_flag=True, help='Run as scheduled daemon (2AM UTC daily)')
@click.option('--dry-run', is_flag=True, help='Fetch records but do NOT update state')
def main(mode, start, end, reset, schedule, dry_run):
    state_manager = StateManager()

    if reset:
        if mode in ['synthetic', 'all']:
            state_manager.reset()
        else:
            state_manager.reset(mode)
        console.print("[yellow]Ingestion state reset.[/yellow]")

    # Initialize adapters
    adapters = []
    if mode in ['synthetic', 'all']:
        adapters.append(SyntheticAdapter())
    elif mode == 'aws':
        adapters.append(AWSCURAdapter())
    elif mode == 'azure':
        adapters.append(AzureCostAdapter())
    elif mode == 'gcp':
        adapters.append(GCPBillingAdapter())

    if schedule:
        scheduler_engine = IngestionScheduler(adapters, state_manager)
        console.print("[bold green]Starting daemon scheduler...[/bold green]")
        scheduler_engine.start_scheduled()
        return

    # Direct run
    results = []
    end_date = date.fromisoformat(end) if end else (utc_now() - timedelta(days=1)).date()
    
    for adapter in adapters:
        cloud = adapter.cloud_provider
        
        # When using SyntheticAdapter for 'all', it natively pulls everything if not filtered
        # But we want per-cloud logs similar to production
        if cloud == 'all':
            for c in ['aws', 'azure', 'gcp']:
                start_d = date.fromisoformat(start) if start else state_manager.get_next_start_date(c, date(2023, 1, 1))
                
                records = adapter.fetch_by_cloud(c, start_d, end_date) # type: ignore
                record_count = len(records)
                
                if not dry_run and record_count > 0:
                    state_manager.update_state(c, end_date, record_count)
                    
                results.append({
                    "cloud": c,
                    "records": record_count,
                    "start": start_d,
                    "end": end_date,
                    "status": "success"
                })
        else:
            start_d = date.fromisoformat(start) if start else state_manager.get_next_start_date(cloud, date(2023, 1, 1))
            
            try:
                records = adapter.fetch_paginated(start_d, end_date)
                record_count = len(records)
                
                if not dry_run and record_count > 0:
                    state_manager.update_state(cloud, end_date, record_count)
                    
                results.append({
                    "cloud": cloud,
                    "records": record_count,
                    "start": start_d,
                    "end": end_date,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "cloud": cloud,
                    "records": 0,
                    "start": start_d,
                    "end": end_date,
                    "status": "error",
                    "error": str(e)
                })

    # Print summary
    table = Table(title="Ingestion Summary")
    table.add_column("Cloud", justify="left")
    table.add_column("Records Fetched", justify="right")
    table.add_column("Date Range", justify="left")
    table.add_column("Status", justify="left")
    
    for r in results:
        status_str = "OK" if r["status"] == "success" else f"Error: {r.get('error')}"
        table.add_row(
            r["cloud"],
            f"{r['records']:,}",
            f"{r['start']} to {r['end']}",
            status_str
        )
        
    console.print(table)

if __name__ == '__main__':
    main()
