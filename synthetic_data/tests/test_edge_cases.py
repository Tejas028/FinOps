import pytest
import datetime
import numpy as np
from generate import generate_month_chunk

@pytest.fixture
def edge_data():
    rng = np.random.default_rng(42)
    # Generate 1 month with edge cases
    start_d = datetime.date(2023, 1, 1)
    end_d = datetime.date(2023, 1, 31)
    df = generate_month_chunk(
        start_d, end_d, {}, ['aws', 'azure', 'gcp'], False, True, rng
    )
    return df

def test_duplicate_records(edge_data):
    df = edge_data
    dupes = df[df['is_duplicate'] == True]
    assert not dupes.empty
    
    # Check that for each duplicate, there is an exact match for service, usage_date, etc.
    for _, dup in dupes.head(5).iterrows():
        matches = df[
            (df['cloud_provider'] == dup['cloud_provider']) &
            (df['service'] == dup['service']) &
            (df['usage_date'] == dup['usage_date']) &
            (df['original_cost'] == dup['original_cost'])
        ]
        # Should be exactly 2 matches usually
        assert len(matches) >= 2

def test_backdated_records(edge_data):
    df = edge_data
    backdated = df[df['is_backdated'] == True]
    assert not backdated.empty
    
    for _, row in backdated.iterrows():
        udate = datetime.datetime.fromisoformat(row['usage_date']).date()
        idate = datetime.datetime.fromisoformat(row['ingested_at'].replace('Z', '+00:00')).date()
        assert udate < idate - datetime.timedelta(days=2)

def test_negative_cost(edge_data):
    df = edge_data
    # "tags must include credit_type"
    negatives = df[df['cost_usd'] < 0]
    assert not negatives.empty
    for _, row in negatives.iterrows():
        assert 'credit_type' in row['tags']
