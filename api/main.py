from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import time
import logging

from api.routers import health, billing, anomalies, forecasts, attribution, alerts
from api.dependencies import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cloud FinOps Intelligence API",
    version="0.1.0",
    description="AI-Powered Multi-Cloud Cost Anomaly Detection & Forecasting",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    # Return a 200 with empty data structure to keep UI alive but showing 'No Data'
    # instead of a broken 500 state
    response = JSONResponse(
        status_code=200,
        content={"data": [], "total": 0, "page": 1, "page_size": 20, "has_next": False, "error": str(exc)}
    )
    # Ensure CORS headers are included even on exception responses
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Mount all routers
app.include_router(health.router,      prefix="",            tags=["Health"])
app.include_router(billing.router,     prefix="/billing",    tags=["Billing"])
app.include_router(anomalies.router,   prefix="/anomalies",  tags=["Anomalies"])
app.include_router(forecasts.router,   prefix="/forecasts",  tags=["Forecasts"])
app.include_router(attribution.router, prefix="/attribution",tags=["Attribution"])
app.include_router(alerts.router,      prefix="/alerts",     tags=["Alerts"])

@app.on_event("startup")
async def startup_event():
    db = get_db()
    connected = db.health_check()
    logger.info(f"FinOps API started. DB connected: {connected}")
