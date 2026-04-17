from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import hashlib
import json
import logging
import os
from groq import Groq
from api.config import GROQ_API_KEY
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache
_insight_cache: Dict[str, str] = {}

class InsightResponse(BaseModel):
    insight: str
    available: bool

class AttributionInsightRequest(BaseModel):
    cloud_provider: str
    service_category: str
    date: str
    total_cost_usd: float
    shap_values: dict
    top_driver_1: Optional[str] = None
    top_driver_1_value: Optional[float] = None
    top_driver_2: Optional[str] = None
    top_driver_2_value: Optional[float] = None
    top_driver_3: Optional[str] = None
    top_driver_3_value: Optional[float] = None

class AnomalyInsightRequest(BaseModel):
    cloud_provider: str
    service: str
    date: str
    actual_cost: float
    expected_cost: float
    deviation_pct: float
    severity: str
    detection_method: str
    z_score: Optional[float] = None

class DailySummaryRequest(BaseModel):
    date_range_start: str
    date_range_end: str
    total_spend: float
    anomaly_count: int
    critical_count: int
    high_count: int
    forecast_30d: float
    by_cloud: dict
    top_anomaly_cloud: Optional[str] = None
    unresolved_alerts: int

def _cache_key(data: dict) -> str:
    return hashlib.md5(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()

def _explain_feature(feature_name: str) -> str:
    """
    Maps raw SHAP feature names to plain English descriptions
    for the Groq prompt.
    """
    mapping = {
        "cost_lag_1d":      "yesterday's cost level",
        "cost_lag_7d":      "cost level 7 days ago",
        "cost_lag_30d":     "cost level 30 days ago",
        "rolling_mean_7d":  "7-day average spend",
        "rolling_mean_30d": "30-day average spend",
        "rolling_std_7d":   "spend volatility over 7 days",
        "rolling_std_30d":  "spend volatility over 30 days",
        "pct_change_1d":    "day-over-day % change",
        "pct_change_7d":    "week-over-week % change",
        "pct_change_30d":   "month-over-month % change",
        "z_score_30d":      "how far costs deviate from the 30-day norm",
        "day_of_week":      "day of week effect",
        "day_of_month":     "day of month effect",
        "week_of_year":     "week of year seasonality",
        "month":            "monthly seasonality",
        "is_weekend":       "weekend usage pattern",
        "is_month_start":   "start-of-month billing pattern",
        "is_month_end":     "end-of-month billing pattern",
        "record_count":     "number of billing line items",
    }
    return mapping.get(feature_name, feature_name.replace("_", " "))

async def call_groq(system_prompt: str, user_message: str) -> str:
    if not GROQ_API_KEY:
        return "AI insights unavailable — GROQ_API_KEY not configured."
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message}
            ],
            max_tokens=150,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return f"Insight generation failed: {str(e)}"

@router.post("/attribution", response_model=InsightResponse)
async def get_attribution_insight(request: AttributionInsightRequest):
    key = _cache_key(request.model_dump())
    if key in _insight_cache:
        return InsightResponse(insight=_insight_cache[key], available=True)

    system_prompt = """
    You are a FinOps analyst assistant. You explain cloud cost
    attribution data in plain English for engineering and finance
    teams. Be concise, specific, and actionable. Never use
    jargon without explanation. Do not mention SHAP, LightGBM,
    or machine learning terminology — translate everything into
    business language. Always respond in 2-3 sentences maximum.
    """

    drivers_info = []
    drivers_info.append(f"1. {request.top_driver_1}: {request.top_driver_1_value:+.2f} ({_explain_feature(request.top_driver_1)})")
    
    if request.top_driver_2:
        drivers_info.append(f"2. {request.top_driver_2}: {request.top_driver_2_value:+.2f} ({_explain_feature(request.top_driver_2)})")
    if request.top_driver_3:
        drivers_info.append(f"3. {request.top_driver_3}: {request.top_driver_3_value:+.2f} ({_explain_feature(request.top_driver_3)})")

    user_message = f"""
    On {request.date}, {request.cloud_provider.upper()} {request.service_category} costs
    were ${request.total_cost_usd:,.2f}.

    The top factors driving this cost level were:
    {"\n    ".join(drivers_info)}

    Explain in plain English why costs are at this level and
    whether this appears to be a one-time event or a trend.
    Keep your response to 2-3 sentences.
    """

    insight = await call_groq(system_prompt, user_message)
    if GROQ_API_KEY and not insight.startswith("Insight generation failed"):
        _insight_cache[key] = insight

    return InsightResponse(
        insight=insight,
        available=bool(GROQ_API_KEY)
    )

@router.post("/anomaly", response_model=InsightResponse)
async def get_anomaly_insight(request: AnomalyInsightRequest):
    key = _cache_key(request.model_dump())
    if key in _insight_cache:
        return InsightResponse(insight=_insight_cache[key], available=True)

    system_prompt = """
    You are a FinOps analyst assistant. You explain cloud cost
    anomalies in plain English for engineering and finance teams.
    Be concise, direct, and actionable. Focus on what the anomaly
    means in business terms and suggest one concrete investigation
    step. Respond in 2-3 sentences maximum. Never mention
    statistical or ML terminology directly.
    """

    user_message = f"""
    A {request.severity} cost anomaly was detected for {request.cloud_provider.upper()}
    {request.service} on {request.date}.

    Actual spend: ${request.actual_cost:,.2f}
    Expected spend: ${request.expected_cost:,.2f}
    Deviation: {request.deviation_pct:+.1f}%
    {'Statistical confidence: z-score of ' + str(round(request.z_score,2))
     if request.z_score else ''}

    In 2-3 sentences: explain what this anomaly likely means in
    business terms, and suggest one specific action an engineer
    or FinOps analyst should take to investigate.
    """

    insight = await call_groq(system_prompt, user_message)
    if GROQ_API_KEY and not insight.startswith("Insight generation failed"):
        _insight_cache[key] = insight

    return InsightResponse(
        insight=insight,
        available=bool(GROQ_API_KEY)
    )

@router.post("/daily-summary", response_model=InsightResponse)
async def get_daily_summary(request: DailySummaryRequest):
    key = _cache_key(request.model_dump())
    if key in _insight_cache:
        return InsightResponse(insight=_insight_cache[key], available=True)

    system_prompt = """
    You are a FinOps analyst writing a brief daily summary for an
    executive or engineering lead. Be factual, specific with
    numbers, and highlight the most important action item.
    Write exactly 3 sentences: one on current spend status,
    one on anomaly/risk status, one on the top recommended action.
    Use plain business language, no technical jargon.
    """

    user_message = f"""
    FinOps platform summary for {request.date_range_start} to {request.date_range_end}:

    - Total cloud spend: ${request.total_spend:,.0f}
    - Anomalies detected: {request.anomaly_count}
      ({request.critical_count} critical, {request.high_count} high severity)
    - 30-day spend forecast: ${request.forecast_30d:,.0f}
    - Spend by cloud: {', '.join(f"{k.upper()}: ${v:,.0f}"
      for k,v in request.by_cloud.items())}
    - Unresolved alerts: {request.unresolved_alerts}
    - Highest risk cloud: {request.top_anomaly_cloud or 'none identified'}

    Write a 3-sentence executive summary of current cloud spend
    health and the single most important action to take today.
    """

    insight = await call_groq(system_prompt, user_message)
    if GROQ_API_KEY and not insight.startswith("Insight generation failed"):
        _insight_cache[key] = insight

    return InsightResponse(
        insight=insight,
        available=bool(GROQ_API_KEY)
    )
