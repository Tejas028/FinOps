import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    _pool: pool.ThreadedConnectionPool = None

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the connection pool. Call once at startup.
        Prioritizes DATABASE_URL if present (standard for Render/Heroku).
        Otherwise reads individual params.
        """
        if cls._pool is not None:
            return

        min_conn = int(os.getenv("TIMESCALE_POOL_MIN", 2))
        max_conn = int(os.getenv("TIMESCALE_POOL_MAX", 10))
        
        db_url = os.getenv("DATABASE_URL")
        
        try:
            if db_url:
                # Use DSN string for initialization
                cls._pool = pool.ThreadedConnectionPool(
                    minconn=min_conn,
                    maxconn=max_conn,
                    dsn=db_url
                )
                logging.info("Database connection pool initialized using DATABASE_URL.")
            else:
                cls._pool = pool.ThreadedConnectionPool(
                    minconn=min_conn,
                    maxconn=max_conn,
                    host=os.getenv("TIMESCALE_HOST", "localhost"),
                    port=os.getenv("TIMESCALE_PORT", "5432"),
                    dbname=os.getenv("TIMESCALE_DB", "finops"),
                    user=os.getenv("TIMESCALE_USER", "finops_user"),
                    password=os.getenv("TIMESCALE_PASSWORD", "finops_pass")
                )
                logging.info("Database connection pool initialized using individual params.")
        except Exception as e:
            logging.error(f"Failed to initialize database pool: {e}")
            raise

    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Context manager: yields a connection from the pool.
        Commits on success, rolls back on exception.
        Returns connection to pool on exit.
        """
        if cls._pool is None:
            cls.initialize()
            
        conn = cls._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cls._pool.putconn(conn)

    @classmethod
    def close(cls) -> None:
        """Close all connections in the pool."""
        if cls._pool is not None:
            cls._pool.closeall()
            cls._pool = None

    @classmethod
    def health_check(cls) -> bool:
        """Execute SELECT 1. Return True if DB is reachable."""
        try:
            with cls.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    return True
        except Exception:
            return False
