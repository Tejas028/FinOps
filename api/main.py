from fastapi import FastAPI

app = FastAPI(
    title="Cloud FinOps Intelligence API",
    version="0.1.0",
    description="AI-Powered Multi-Cloud Cost Anomaly Detection & Spend Forecasting"
)

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
