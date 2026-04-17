from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import time
import logging

from api.routers import health, billing, anomalies, forecasts, attribution, alerts, insights
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

import os

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    
    # Check if request origin is allowed
    origin = request.headers.get("origin")
    allow_origin = origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0]

    response = JSONResponse(
        status_code=200,
        content={"data": [], "total": 0, "page": 1, "page_size": 20, "has_next": False, "error": str(exc)}
    )
    response.headers["Access-Control-Allow-Origin"] = allow_origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.get("/")
async def root():
    return {
        "message": "Cloud FinOps Intelligence API is running",
        "docs": "/docs",
        "health": "/health",
        "status": "active"
    }

# Mount all routers
app.include_router(health.router,      prefix="",            tags=["Health"])
app.include_router(billing.router,     prefix="/billing",    tags=["Billing"])
app.include_router(anomalies.router,   prefix="/anomalies",  tags=["Anomalies"])
app.include_router(forecasts.router,   prefix="/forecasts",  tags=["Forecasts"])
app.include_router(attribution.router, prefix="/attribution",tags=["Attribution"])
app.include_router(alerts.router,      prefix="/alerts",     tags=["Alerts"])
app.include_router(insights.router,    prefix="/insights",   tags=["AI Insights"])

@app.on_event("startup")
async def startup_event():
    db = get_db()
    connected = db.health_check()
    logger.info(f"FinOps API started. DB connected: {connected}")
