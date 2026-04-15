import pytest
import os
from datetime import date
from ingestion.state_manager import StateManager

@pytest.fixture
def state_manager(tmpdir):
    sf = tmpdir.join("state.json")
    return StateManager(state_file=str(sf))

def test_initial_state_returns_none(state_manager):
    assert state_manager.get_last_ingested_date("aws") is None

def test_update_state_roundtrip(state_manager):
    d = date(2023, 5, 20)
    state_manager.update_state("aws", d, 100)
    assert state_manager.get_last_ingested_date("aws") == d
    assert state_manager.state["aws"]["total_records"] == 100

def test_next_start_date_uses_fallback(state_manager):
    fallback = date(2023, 1, 1)
    res = state_manager.get_next_start_date("azure", fallback)
    assert res == fallback

def test_next_start_date_uses_last_plus_one(state_manager):
    d = date(2023, 5, 20)
    state_manager.update_state("aws", d, 100)
    
    res = state_manager.get_next_start_date("aws", date(2023, 1, 1))
    assert res == date(2023, 5, 21)

def test_reset_clears_state(state_manager):
    state_manager.update_state("gcp", date(2023, 5, 20), 50)
    assert state_manager.get_last_ingested_date("gcp") is not None
    
    state_manager.reset("gcp")
    assert state_manager.get_last_ingested_date("gcp") is None
    
    state_manager.update_state("gcp", date(2023, 5, 20), 50)
    state_manager.update_state("aws", date(2023, 5, 20), 50)
    state_manager.reset()
    assert state_manager.get_last_ingested_date("gcp") is None
    assert state_manager.get_last_ingested_date("aws") is None
