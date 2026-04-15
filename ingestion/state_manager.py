import json
import os
from datetime import date, timedelta
from typing import Optional

class StateManager:
    def __init__(self, state_file: str = "ingestion/ingestion_state.json"):
        self.state_file = state_file
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {}

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_last_ingested_date(self, cloud_provider: str) -> Optional[date]:
        """Return last ingested date, or None if never run."""
        cp_state = self.state.get(cloud_provider)
        if cp_state and "last_ingested_date" in cp_state:
            return date.fromisoformat(cp_state["last_ingested_date"])
        return None

    def update_state(self, cloud_provider: str, last_date: date, records_ingested: int) -> None:
        """Atomically update state for one cloud provider."""
        cp_state = self.state.get(cloud_provider, {"last_ingested_date": None, "total_records": 0})
        cp_state["last_ingested_date"] = last_date.isoformat()
        cp_state["total_records"] += records_ingested
        self.state[cloud_provider] = cp_state
        self._save_state()

    def get_next_start_date(self, cloud_provider: str, fallback_start: date) -> date:
        """
        Return last_ingested_date + 1 day if state exists,
        else return fallback_start. Prevents re-ingestion.
        """
        last_date = self.get_last_ingested_date(cloud_provider)
        if last_date:
            return last_date + timedelta(days=1)
        return fallback_start

    def reset(self, cloud_provider: Optional[str] = None) -> None:
        """Reset state for one or all clouds (for re-ingestion runs)."""
        if cloud_provider:
            if cloud_provider in self.state:
                del self.state[cloud_provider]
        else:
            self.state = {}
        self._save_state()
