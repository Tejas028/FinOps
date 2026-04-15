import pytest
import datetime
import numpy as np
import pandas as pd
from generator.schema import BillingRecord
from generate import generate_month_chunk
from generator.anomaly_injector import build_anomaly_schedule

@pytest.fixture
def chunk_data():
    rng = np.random.default_rng(42)
    schedule, _ = build_anomaly_schedule()
    start_d = datetime.date(2023, 1, 1)
    end_d = datetime.date(2023, 1, 3)
    df = generate_month_chunk(
        start_d, end_d, schedule, ['aws', 'azure', 'gcp'], True, True, rng
    )
    return df

def test_pydantic_schema(chunk_data):
    records = chunk_data.to_dict('records')
    for r in records:
        BillingRecord(**r)  # Should not raise exception
        
def test_no_nan_cost(chunk_data):
    assert not chunk_data['cost_usd'].isnull().any()
    assert not np.isinf(chunk_data['cost_usd']).any()

def test_ingested_at_logic(chunk_data):
    for _, row in chunk_data.iterrows():
        udate = datetime.datetime.fromisoformat(row['usage_date']).date()
        idate = datetime.datetime.fromisoformat(row['ingested_at'].replace('Z', '+00:00')).date()
        assert udate <= idate

def test_exchange_rate_logic(chunk_data):
    for _, row in chunk_data.iterrows():
        calc_cost = row['original_cost'] * row['exchange_rate']
        assert abs(calc_cost - row['cost_usd']) < 0.01
