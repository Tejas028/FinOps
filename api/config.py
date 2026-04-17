import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.getenv("TIMESCALE_HOST", "127.0.0.1")
DB_PORT     = int(os.getenv("TIMESCALE_PORT", "5433"))
DB_NAME     = os.getenv("TIMESCALE_DB", "finops")
DB_USER     = os.getenv("TIMESCALE_USER", "finops_user")
DB_PASSWORD = os.getenv("TIMESCALE_PASSWORD", "finops_pass")

APP_VERSION = "0.1.0"
API_HOST    = os.getenv("API_HOST", "0.0.0.0")
API_PORT    = int(os.getenv("API_PORT", "8000"))
LOG_LEVEL   = os.getenv("LOG_LEVEL", "INFO")
