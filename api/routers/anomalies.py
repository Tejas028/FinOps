from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import date
import psycopg2.extras

from api.dependencies import get_db, PaginationParams
from api.schemas.responses import PaginatedResponse, AnomalyListItem, AnomalySummary

router = APIRouter()

@router.get("", response_model=PaginatedResponse[AnomalyListItem])
async def list_anomalies(
    start_date: date,
    end_date: date,
    cloud_provider: Optional[List[str]] = Query(None),
    severity: Optional[List[str]] = Query(None),
    detection_method: Optional[str] = None,
    service: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db = Depends(get_db)
):
    query = """
    SELECT 
        ar.anomaly_id,
        ar.record_id,
        ar.detection_method,
        ar.severity,
        ar.z_score,
        ar.expected_cost,
        ar.actual_cost,
        ar.deviation_pct,
        ar.detected_at,
        ar.cloud_provider,
        ar.service,
        NULL as region,
        ar.usage_date
    FROM anomalies ar
    WHERE ar.usage_date BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    
    if cloud_provider:
        query += " AND ar.cloud_provider = ANY(%s)"
        params.append(cloud_provider)
    if severity:
        query += " AND ar.severity = ANY(%s)"
        params.append(severity)
    if detection_method:
        query += " AND ar.detection_method = %s"
        params.append(detection_method)
    if service:
        query += " AND ar.service = %s"
        params.append(service)
        
    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({query}) as sub"
    
    query += " ORDER BY ar.detected_at DESC LIMIT %s OFFSET %s"
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

@router.get("/summary", response_model=AnomalySummary)
async def get_anomaly_summary(
    start_date: date,
    end_date: date,
    db = Depends(get_db)
):
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. Severity
            cur.execute("""
                SELECT severity, COUNT(*) as count 
                FROM anomalies
                WHERE usage_date BETWEEN %s AND %s
                GROUP BY severity
            """, (start_date, end_date))
            by_severity = {r['severity']: r['count'] for r in cur.fetchall()}
            
            # 2. Cloud
            cur.execute("""
                SELECT cloud_provider, COUNT(*) as count 
                FROM anomalies
                WHERE usage_date BETWEEN %s AND %s
                GROUP BY cloud_provider
            """, (start_date, end_date))
            by_cloud = {r['cloud_provider']: r['count'] for r in cur.fetchall()}
            
            # 3. Type (detection_method as proxy if anomaly_type missing)
            cur.execute("""
                SELECT detection_method as anomaly_type, COUNT(*) as count 
                FROM anomalies
                WHERE usage_date BETWEEN %s AND %s
                GROUP BY detection_method
            """, (start_date, end_date))
            by_type = {r['anomaly_type']: r['count'] for r in cur.fetchall()}
            
            total = sum(by_severity.values())
            
    return AnomalySummary(
        total_anomalies=total,
        by_severity=by_severity,
        by_cloud=by_cloud,
        by_type=by_type,
        date_range={"start": str(start_date), "end": str(end_date)}
    )

@router.get("/recent", response_model=List[AnomalyListItem])
async def get_recent_anomalies(
    limit: int = Query(10, ge=1, le=50),
    db = Depends(get_db)
):
    query = """
    SELECT 
        ar.anomaly_id,
        ar.record_id,
        ar.detection_method,
        ar.severity,
        ar.z_score,
        ar.expected_cost,
        ar.actual_cost,
        ar.deviation_pct,
        ar.detected_at,
        ar.cloud_provider,
        ar.service,
        -- ar table doesn't have region, join would be needed if region required
        NULL as region, 
        ar.usage_date
    FROM anomalies ar
    ORDER BY ar.detected_at DESC
    LIMIT %s
    """
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (limit,))
            rows = cur.fetchall()
    return rows

@router.get("/{anomaly_id}", response_model=AnomalyListItem)
async def get_anomaly_detail(
    anomaly_id: str,
    db = Depends(get_db)
):
    query = """
    SELECT 
        ar.anomaly_id,
        ar.record_id,
        ar.detection_method,
        ar.severity,
        ar.z_score,
        ar.expected_cost,
        ar.actual_cost,
        ar.deviation_pct,
        ar.detected_at,
        ar.cloud_provider,
        ar.service,
        NULL as region,
        ar.usage_date
    FROM anomalies ar
    WHERE ar.anomaly_id = %s
    """
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, (anomaly_id,))
            row = cur.fetchone()
            
    if not row:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return row
