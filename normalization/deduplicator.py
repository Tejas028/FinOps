import hashlib
from typing import List, Set, Tuple
from shared.schemas.billing import BillingRecord

def generate_fingerprint(record: BillingRecord) -> str:
    components = [
        str(record.cloud_provider),
        str(record.account_id),
        str(record.service),
        record.usage_date.isoformat(),
        str(round(record.cost_usd, 6))
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()

class Deduplicator:
    def __init__(self):
        self._seen: Set[str] = set()

    def is_duplicate(self, fingerprint: str) -> bool:
        """Return True if fingerprint has been seen before."""
        return fingerprint in self._seen

    def mark_seen(self, fingerprint: str) -> None:
        """Add fingerprint to the seen set."""
        self._seen.add(fingerprint)

    def filter(self, records: List[BillingRecord]) -> Tuple[List[BillingRecord], int]:
        """
        Filter a list of BillingRecords, removing duplicates.
        Returns: (deduplicated_records, count_of_duplicates_removed)
        The seen set is updated during this call.
        """
        deduplicated = []
        dups_removed = 0
        for record in records:
            fp = generate_fingerprint(record)
            if self.is_duplicate(fp):
                dups_removed += 1
            else:
                self.mark_seen(fp)
                deduplicated.append(record)
        return deduplicated, dups_removed

    def reset(self) -> None:
        """Clear the seen set (for fresh runs)."""
        self._seen.clear()
