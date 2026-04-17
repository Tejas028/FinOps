from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import date
import psycopg2.extras

from api.dependencies import get_db, PaginationParams
from api.schemas.responses import PaginatedResponse, BillingSummary, SpendByDimension
from pydantic import BaseModel

class BillingBounds(BaseModel):
    min_date: str
    max_date: str

router = APIRouter()

@router.get("/summary", response_model=PaginatedResponse[BillingSummary])
async def get_billing_summary(
    start_date: date,
    end_date: date,
    cloud_provider: Optional[List[str]] = Query(None),
    service: Optional[str] = None,
    region: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db = Depends(get_db)
):
    query = """
    SELECT 
        usage_date,
        cloud_provider,
        service_category as service,
        region,
        SUM(cost_usd) as total_cost_usd,
        COUNT(*) as record_count,
        SUM(CASE WHEN anomaly_flag THEN 1 ELSE 0 END) as anomaly_count
    FROM billing_records
    WHERE usage_date BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    
    if cloud_provider:
        query += " AND cloud_provider = ANY(%s)"
        params.append(cloud_provider)
    if service:
        query += " AND service_category = %s"
        params.append(service)
    if region:
        query += " AND region = %s"
        params.append(region)
        
    query += " GROUP BY usage_date, cloud_provider, service_category, region"
    
    # Get total count for pagination
    count_query = f"SELECT COUNT(*) FROM ({query}) as sub"
    
    query += " ORDER BY usage_date DESC LIMIT %s OFFSET %s"
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

@router.get("/bounds", response_model=BillingBounds)
async def get_billing_bounds(db = Depends(get_db)):
    query = """
    SELECT
      MIN(usage_date)::text AS min_date,
      MAX(usage_date)::text AS max_date
    FROM billing_records
    """
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            row = cur.fetchone()
            
    # Fallback to sensible defaults if empty
    return BillingBounds(
        min_date=row['min_date'] if row and row['min_date'] else "2023-01-01",
        max_date=row['max_date'] if row and row['max_date'] else "2024-12-31"
    )

@router.get("/by-cloud", response_model=List[SpendByDimension])
async def get_spend_by_cloud(
    start_date: date,
    end_date: date,
    db = Depends(get_db)
):
    query = """
    WITH totals AS (
        SELECT SUM(cost_usd) as grand_total FROM billing_records 
        WHERE usage_date BETWEEN %s AND %s
    )
    SELECT 
        cloud_provider as dimension,
        SUM(cost_usd) as total_cost_usd,
        (SUM(cost_usd) / NULLIF((SELECT grand_total FROM totals), 0)) * 100 as pct_of_total,
        COUNT(*) as record_count
    FROM billing_records
    WHERE usage_date BETWEEN %s AND %s
    GROUP BY cloud_provider
    ORDER BY total_cost_usd DESC
    """
    params = [start_date, end_date, start_date, end_date]
    
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
    return rows

@router.get("/by-service", response_model=List[SpendByDimension])
async def get_spend_by_service(
    start_date: date,
    end_date: date,
    cloud_provider: Optional[str] = None,
    top_n: int = 10,
    db = Depends(get_db)
):
    query = """
    WITH totals AS (
        SELECT SUM(cost_usd) as grand_total FROM billing_records 
        WHERE usage_date BETWEEN %s AND %s
    )
    SELECT 
        service_category as dimension,
        SUM(cost_usd) as total_cost_usd,
        (SUM(cost_usd) / NULLIF((SELECT grand_total FROM totals), 0)) * 100 as pct_of_total,
        COUNT(*) as record_count
    FROM billing_records
    WHERE usage_date BETWEEN %s AND %s
    """
    params = [start_date, end_date, start_date, end_date]
    
    if cloud_provider:
        query += " AND cloud_provider = %s"
        params.append(cloud_provider)
        
    query += " GROUP BY service_category ORDER BY total_cost_usd DESC LIMIT %s"
    params.append(top_n)
    
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
    return rows

@router.get("/trend")
async def get_spend_trend(
    start_date: date,
    end_date: date,
    cloud_provider: Optional[str] = None,
    granularity: str = "day",
    db = Depends(get_db)
):
    if granularity not in ["day", "week", "month"]:
        granularity = "day"
        
    trunc_op = f"DATE_TRUNC('{granularity}', usage_date)"
    
    query = f"""
    SELECT 
        {trunc_op}::text as period,
        SUM(cost_usd) as total_cost_usd,
        COUNT(*) as record_count
    FROM billing_records
    WHERE usage_date BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    
    if cloud_provider:
        query += " AND cloud_provider = %s"
        params.append(cloud_provider)
        
    query += f" GROUP BY period ORDER BY period ASC"
    
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
    return rows
