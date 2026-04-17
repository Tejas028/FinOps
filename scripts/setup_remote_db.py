import psycopg2
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SQL_FILES = [
    "storage/init_db/init.sql",
    "features/init_db/features_schema.sql",
    "detection/init_db/detection_schema.sql",
    "forecasting/init_db/forecasts_schema.sql",
    "attribution/init_db/attribution_schema.sql",
    "alerting/init_db/alerts_schema.sql"
]

def setup_remote_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL environment variable not set.")
        sys.exit(1)

    print(f"Connecting to remote database...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()

        # 1. Enable TimescaleDB first
        print("Enabling timescaledb extension...")
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
        except Exception as e:
            print(f"Warning: Could not enable timescaledb extension (might already be enabled or not supported): {e}")

        # 2. Run schema files
        for sql_path in SQL_FILES:
            if not os.path.exists(sql_path):
                print(f"Warning: File not found: {sql_path}")
                continue
            
            print(f"Executing {sql_path}...")
            with open(sql_path, 'r') as f:
                sql_content = f.read()
                if sql_content.strip():
                    cur.execute(sql_content)
        
        print("\nSuccess! Remote database schema initialized.")
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_remote_db()
