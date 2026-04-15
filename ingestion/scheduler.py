import logging
from typing import List, Dict, Any
from datetime import date, datetime, timedelta, timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from shared.utils.date_utils import utc_now
from .base_adapter import BaseIngestionAdapter
from .state_manager import StateManager

class IngestionScheduler:

    def __init__(self, adapters: List[BaseIngestionAdapter], state_manager: StateManager):
        self.adapters = adapters
        self.state = state_manager
        self.scheduler = BlockingScheduler()

    def run_ingestion(self, adapter: BaseIngestionAdapter) -> dict:
        """
        Core ingestion logic for one adapter:
        1. Get start_date from state_manager (or config fallback)
        2. Set end_date = yesterday (UTC)
        3. Call adapter.fetch(start_date, end_date)
        4. Log record count + date range
        5. Update state_manager on success
        6. Return: {"cloud": str, "records": int, "start": date, "end": date,
                    "status": "success"|"error", "error": Optional[str]}
        """
        cloud = adapter.cloud_provider
        try:
            # Synthetic adapter overrides might return 'all', but conceptually we ingest per-cloud.
            # Handle properly.
            
            # fallback_start = date(2023, 1, 1) by default or from config
            fallback_start = date(2023, 1, 1)
            start_date = self.state.get_next_start_date(cloud, fallback_start)
            end_date = (utc_now() - timedelta(days=1)).date()
            
            if start_date > end_date:
                return {
                    "cloud": cloud,
                    "records": 0,
                    "start": start_date,
                    "end": end_date,
                    "status": "success",
                    "error": None
                }
                
            records = adapter.fetch_paginated(start_date, end_date)
            record_count = len(records)
            
            if record_count > 0:
                self.state.update_state(cloud, end_date, record_count)
                
            logging.info(f"Ingested {record_count} records for {cloud} from {start_date} to {end_date}")
            
            return {
                "cloud": cloud,
                "records": record_count,
                "start": start_date,
                "end": end_date,
                "status": "success",
                "error": None
            }
            
        except Exception as e:
            logging.error(f"Error during ingestion for {cloud}: {e}")
            return {
                "cloud": cloud,
                "records": 0,
                "start": start_date, # type: ignore
                "end": end_date, # type: ignore
                "status": "error",
                "error": str(e)
            }

    def run_all(self) -> List[dict]:
        """Run ingestion for all registered adapters. Return list of results."""
        results = []
        for adapter in self.adapters:
            res = self.run_ingestion(adapter)
            results.append(res)
        return results

    def start_scheduled(self, cron_hour: int = 2, cron_minute: int = 0):
        """
        Schedule run_all() daily at cron_hour:cron_minute UTC.
        Default: 2:00 AM UTC (after cloud billing APIs refresh).
        """
        trigger = CronTrigger(hour=cron_hour, minute=cron_minute, timezone=timezone.utc)
        self.scheduler.add_job(self.run_all, trigger=trigger)
        logging.info(f"Started scheduler for ingestion at {cron_hour:02d}:{cron_minute:02d} UTC")
        self.scheduler.start()
