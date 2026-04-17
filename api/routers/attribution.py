from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict
from datetime import date
import psycopg2.extras
import json

from api.dependencies import get_db, PaginationParams
from api.schemas.responses import PaginatedResponse, AttributionListItem

router = APIRouter()

@router.get("", response_model=PaginatedResponse[AttributionListItem])
async def list_attributions(
    start_date: date,
    end_date: date,
    cloud_provider: Optional[str] = None,
    service_category: Optional[str] = None,
    top_driver: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db = Depends(get_db)
):
    query = """
    SELECT 
        attribution_date::text as attribution_date,
        cloud_provider,
        service_category,
        account_id,
        environment,
        team,
        total_cost_usd,
        top_driver_1,
        top_driver_1_value,
        top_driver_2,
        top_driver_2_value,
        top_driver_3,
        top_driver_3_value,
        model_r2_score,
        shap_values
    FROM cost_attributions
    WHERE attribution_date BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    
    if cloud_provider:
        query += " AND cloud_provider = %s"
        params.append(cloud_provider)
    if service_category:
        query += " AND service_category = %s"
        params.append(service_category)
    if top_driver:
        query += " AND (top_driver_1 = %s OR top_driver_2 = %s OR top_driver_3 = %s)"
        params.extend([top_driver, top_driver, top_driver])
        
    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({query}) as sub"
    
    query += " ORDER BY attribution_date DESC LIMIT %s OFFSET %s"
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

@router.get("/services", response_model=List[str])
async def list_attribution_services(db = Depends(get_db)):
    """Returns distinct service categories available in the attribution table."""
    query = "SELECT DISTINCT service_category FROM cost_attributions ORDER BY service_category"
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
    return [r[0] for r in rows]

@router.get("/top-drivers")
async def get_top_drivers(
    start_date: date,
    end_date: date,
    cloud_provider: Optional[str] = None,
    top_n: int = 10,
    db = Depends(get_db)
):
    # Pure SQL approach to aggregate top 3 drivers
    query = """
    WITH all_drivers AS (
        SELECT top_driver_1 as driver, top_driver_1_value as val FROM cost_attributions WHERE attribution_date BETWEEN %s AND %s
        UNION ALL
        SELECT top_driver_2 as driver, top_driver_2_value as val FROM cost_attributions WHERE attribution_date BETWEEN %s AND %s
        UNION ALL
        SELECT top_driver_3 as driver, top_driver_3_value as val FROM cost_attributions WHERE attribution_date BETWEEN %s AND %s
    )
    SELECT 
        driver,
        AVG(val) as avg_shap_value,
        COUNT(*) as appearance_count
    FROM all_drivers
    WHERE driver IS NOT NULL
    """
    params = [start_date, end_date, start_date, end_date, start_date, end_date]
    
    if cloud_provider:
        # We need to add cloud_provider filter to each UNION part if we do it this way
        # or rewrite the CTE
        query = """
        WITH all_drivers AS (
            SELECT top_driver_1 as driver, top_driver_1_value as val FROM cost_attributions 
            WHERE attribution_date BETWEEN %s AND %s AND (%s IS NULL OR cloud_provider = %s)
            UNION ALL
            SELECT top_driver_2 as driver, top_driver_2_value as val FROM cost_attributions 
            WHERE attribution_date BETWEEN %s AND %s AND (%s IS NULL OR cloud_provider = %s)
            UNION ALL
            SELECT top_driver_3 as driver, top_driver_3_value as val FROM cost_attributions 
            WHERE attribution_date BETWEEN %s AND %s AND (%s IS NULL OR cloud_provider = %s)
        )
        SELECT 
            driver,
            AVG(val) as avg_shap_value,
            COUNT(*) as appearance_count
        FROM all_drivers
        WHERE driver IS NOT NULL
        GROUP BY driver
        ORDER BY AVG(ABS(val)) DESC
        LIMIT %s
        """
        cloud = cloud_provider
        params = [
            start_date, end_date, cloud, cloud,
            start_date, end_date, cloud, cloud,
            start_date, end_date, cloud, cloud,
            top_n
        ]
    else:
        query += " GROUP BY driver ORDER BY AVG(ABS(val)) DESC LIMIT %s"
        params.append(top_n)
        
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
    return rows

@router.get("/{cloud_provider}/{service_category}", response_model=List[AttributionListItem])
async def get_group_attribution_series(
    cloud_provider: str,
    service_category: str,
    start_date: date,
    end_date: date,
    db = Depends(get_db)
):
    query = """
    SELECT 
        attribution_date::text as attribution_date,
        cloud_provider,
        service_category,
        account_id,
        environment,
        team,
        total_cost_usd,
        top_driver_1,
        top_driver_1_value,
        top_driver_2,
        top_driver_2_value,
        top_driver_3,
        top_driver_3_value,
        model_r2_score,
        shap_values
    FROM cost_attributions
    WHERE cloud_provider = %s AND service_category = %s
      AND attribution_date BETWEEN %s AND %s
    ORDER BY attribution_date ASC
    """
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (cloud_provider, service_category, start_date, end_date))
            rows = cur.fetchall()
            
    return rows
