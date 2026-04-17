from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict
from datetime import date
import psycopg2.extras

from api.dependencies import get_db, PaginationParams
from api.schemas.responses import PaginatedResponse, ForecastListItem

router = APIRouter()

@router.get("", response_model=PaginatedResponse[ForecastListItem])
async def list_forecasts(
    cloud_provider: Optional[List[str]] = Query(None),
    service: Optional[str] = None,
    horizon_days: Optional[int] = None,
    model_used: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    pagination: PaginationParams = Depends(),
    db = Depends(get_db)
):
    query = "SELECT *, forecast_date::text as forecast_date_display, generated_at::text as generated_at_display FROM forecasts WHERE 1=1"
    params = []
    
    if cloud_provider:
        query += " AND cloud_provider = ANY(%s)"
        params.append(cloud_provider)
    if service:
        query += " AND service = %s"
        params.append(service)
    if horizon_days:
        query += " AND horizon_days <= %s"
        params.append(horizon_days)
    if model_used:
        query += " AND model_used = %s"
        params.append(model_used)
    if start_date:
        query += " AND forecast_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND forecast_date <= %s"
        params.append(end_date)
        
    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({query}) as sub"
    
    query += " ORDER BY forecasts.forecast_date ASC LIMIT %s OFFSET %s"
    params_with_paging = params + [pagination.page_size, pagination.offset]
    
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(count_query, tuple(params))
            total = cur.fetchone()['count']
            
            cur.execute(query, tuple(params_with_paging))
            rows = cur.fetchall()
            
    return PaginatedResponse(
        data=rows,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        has_next=total > (pagination.page * pagination.page_size)
    )

@router.get("/latest", response_model=List[ForecastListItem])
async def get_latest_forecast(
    cloud_provider: Optional[str] = None,
    service: Optional[str] = None,
    horizon_days: int = 30,
    db = Depends(get_db)
):
    """
    Returns the latest forecast series.
    If cloud_provider or service is None, it aggregates (SUM) across that dimension
    using the latest available run for each unique combination.
    """
    where_clauses = ["f.horizon_days <= %s"]
    params = [horizon_days]

    if cloud_provider:
        where_clauses.append("f.cloud_provider = %s")
        params.append(cloud_provider)
    
    if service:
        where_clauses.append("f.service = %s")
        params.append(service)

    where_str = " AND ".join(where_clauses)
    
    # We use a CTE to find the latest run for each cloud/service/horizon combo
    # and then sum them up. 
    # Mandatory fields for ForecastListItem must be filled for validation.
    query = f"""
    WITH latest_runs AS (
        SELECT cloud_provider, service, MAX(generated_at) as last_gen
        FROM forecasts
        GROUP BY cloud_provider, service
    )
    SELECT 
        'aggregated_' || f.forecast_date::text as forecast_id,
        COALESCE(%s, 'All Clouds') as cloud_provider,
        COALESCE(%s, 'All Services') as service,
        NULL as region,
        %s as horizon_days,
        f.forecast_date, 
        f.forecast_date::text as forecast_date_display,
        MAX(f.generated_at)::text as last_updated_display,
        'ensemble' as model_used,
        MAX(f.generated_at) as generated_at,
        SUM(f.predicted_cost) as predicted_cost,
        SUM(f.lower_bound) as lower_bound,
        SUM(f.upper_bound) as upper_bound
    FROM forecasts f
    JOIN latest_runs lr ON f.cloud_provider = lr.cloud_provider 
        AND f.service = lr.service AND f.generated_at = lr.last_gen
    WHERE {where_str}
    GROUP BY f.forecast_date
    ORDER BY f.forecast_date ASC
    """
    
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Need to pass horizon_days for the CTE, 
            # then cloud_provider, service, horizon_days for the static columns,
            # then all params for the WHERE clause.
            all_params = [cloud_provider, service, horizon_days] + params
            cur.execute(query, tuple(all_params))
            rows = cur.fetchall()
            
    return rows

from api.schemas.responses import PaginatedResponse, ForecastListItem, BudgetRiskResponse

@router.get("/budget-risk", response_model=BudgetRiskResponse)
async def get_budget_risk(
    cloud_provider: Optional[str] = None,
    monthly_budget_usd: float = 50000,
    horizon_days: int = 30,
    db = Depends(get_db)
):
    # 1. Get the latest forecast series for all services of this cloud
    # To simplify, we sum up the latest forecasts per service category.
    # We need to find the latest 'run' for each service.
    
    if cloud_provider:
        query = """
        WITH latest_runs AS (
            SELECT service, MAX(generated_at) as last_gen
            FROM forecasts
            WHERE cloud_provider = %s AND horizon_days <= %s
            GROUP BY service
        )
        SELECT 
            forecast_date, 
            SUM(predicted_cost) as predicted_cost,
            SUM(lower_bound) as lower_bound,
            SUM(upper_bound) as upper_bound
        FROM forecasts f
        JOIN latest_runs lr ON f.service = lr.service AND f.generated_at = lr.last_gen
        WHERE f.cloud_provider = %s AND f.horizon_days <= %s
        GROUP BY f.forecast_date
        ORDER BY f.forecast_date ASC
        """
        query_params = (cloud_provider, horizon_days, cloud_provider, horizon_days)
    else:
        query = """
        WITH latest_runs AS (
            SELECT cloud_provider, service, MAX(generated_at) as last_gen
            FROM forecasts
            WHERE horizon_days = %s
            GROUP BY cloud_provider, service
        )
        SELECT 
            forecast_date, 
            SUM(predicted_cost) as predicted_cost,
            SUM(lower_bound) as lower_bound,
            SUM(upper_bound) as upper_bound
        FROM forecasts f
        JOIN latest_runs lr ON f.cloud_provider = lr.cloud_provider 
            AND f.service = lr.service AND f.generated_at = lr.last_gen
        WHERE f.horizon_days <= %s
        GROUP BY f.forecast_date
        ORDER BY f.forecast_date ASC
        """
        query_params = (horizon_days, horizon_days)
    
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, query_params)
            rows = cur.fetchall()
            
    if not rows:
        raise HTTPException(status_code=404, detail="No forecasts found for risk analysis")
        
    cum_pred = 0.0
    cum_lower = 0.0
    cum_upper = 0.0
    
    breach_date = None
    
    for r in rows:
        cum_pred += r['predicted_cost']
        cum_lower += r['lower_bound']
        cum_upper += r['upper_bound']
        
        if not breach_date and cum_upper >= monthly_budget_usd:
            breach_date = r['forecast_date']
            
    # Logic:
    # "none"     if upper_total < monthly_budget
    # "possible" if lower_total < monthly_budget <= predicted_total
    # "likely"   if predicted_total < monthly_budget <= upper_total
    # "certain"  if lower_total >= monthly_budget
    
    if cum_upper < monthly_budget_usd:
        risk = "none"
    elif cum_lower < monthly_budget_usd <= cum_pred:
        risk = "possible"
    elif cum_pred < monthly_budget_usd <= cum_upper:
        risk = "likely"
    else: # cum_lower >= monthly_budget_usd
        risk = "certain"
        
    import datetime
    days_to_breach = None
    if breach_date:
        # Assuming forecast starts tomorrow or near today
        days_to_breach = (breach_date - date.today()).days
        
    return {
        "cloud_provider": cloud_provider,
        "monthly_budget_usd": monthly_budget_usd,
        "projected_monthly_cost": round(cum_pred, 2),
        "breach_risk": risk,
        "breach_date": str(breach_date) if breach_date else None,
        "days_to_breach": days_to_breach,
        "confidence_pct": 95.0
    }
