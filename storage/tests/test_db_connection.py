import pytest
import threading
from storage.db import DatabaseManager

@pytest.fixture(autouse=True)
def setup_teardown():
    DatabaseManager.initialize()
    yield
    DatabaseManager.close()

def test_health_check():
    """Test 2: health_check() returns True with DB running"""
    import os
    if not os.getenv("TIMESCALE_HOST"):
        pytest.skip("No DB host configured.")
    assert DatabaseManager.health_check() is True

def test_initialize():
    """Test 1: DatabaseManager.initialize() succeeds without error"""
    # Already called in fixture, just asserting pool exists
    assert DatabaseManager._pool is not None

def test_get_connection():
    """Test 3: get_connection() context manager yields a valid connection"""
    with DatabaseManager.get_connection() as conn:
        assert not conn.closed
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1
    # connection goes back to pool, not fully closed
    assert DatabaseManager._pool is not None

def test_concurrent_connections():
    """Test 4: Two concurrent get_connection() calls both succeed"""
    def query_db():
        with DatabaseManager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                assert cur.fetchone()[0] == 1
                
    t1 = threading.Thread(target=query_db)
    t2 = threading.Thread(target=query_db)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
