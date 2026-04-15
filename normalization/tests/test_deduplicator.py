from datetime import date
from shared.schemas.billing import BillingRecord
from normalization.deduplicator import Deduplicator, generate_fingerprint

def dummy_record(idx: int) -> BillingRecord:
    return BillingRecord(
        record_id=f"{idx}",
        cloud_provider="aws",
        account_id="acc",
        service="EC2",
        usage_date=date(2023, 1, 1),
        cost_usd=10.0 + idx,
        original_cost=10.0 + idx,
        original_currency="USD",
        exchange_rate=1.0,
        tags='{}',
        ingested_at=date(2023, 1, 1)
    )

def test_unique_records_pass_through():
    d = Deduplicator()
    recs = [dummy_record(1), dummy_record(2)]
    out, dups = d.filter(recs)
    assert len(out) == 2
    assert dups == 0

def test_duplicate_fingerprint_is_blocked():
    d = Deduplicator()
    # same record twice
    recs = [dummy_record(1), dummy_record(1)]
    out, dups = d.filter(recs)
    assert len(out) == 1
    assert dups == 1

def test_reset_clears_seen_set():
    d = Deduplicator()
    d.filter([dummy_record(1)])
    assert len(d._seen) == 1
    d.reset()
    assert len(d._seen) == 0

def test_filter_returns_correct_tuple():
    d = Deduplicator()
    recs = [dummy_record(1), dummy_record(1), dummy_record(2)]
    out, dups = d.filter(recs)
    assert isinstance(out, list)
    assert isinstance(dups, int)
    assert len(out) == 2
    assert dups == 1

def test_fingerprint_is_deterministic():
    r = dummy_record(1)
    fp1 = generate_fingerprint(r)
    fp2 = generate_fingerprint(r)
    assert fp1 == fp2
