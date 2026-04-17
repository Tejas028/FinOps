from fastapi import APIRouter, Query, Depends, HTTPException, Path
from typing import List, Optional, Dict
from datetime import date
from pydantic import BaseModel

from api.schemas.responses import PaginatedResponse, AlertListItem
from alerting.repository import AlertRepository
from storage.db import DatabaseManager

router = APIRouter()

# Dependency to ensure DB is connected, though repository gets its own connection
def get_alert_repo():
    return AlertRepository()

class AlertSummaryResponse(BaseModel):
    total: int
    unresolved: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    by_cloud: Dict[str, int]

@router.get("", response_model=PaginatedResponse[AlertListItem])
async def get_alerts(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    cloud_provider: Optional[str] = Query(None, description="Filter by cloud"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    is_resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=1000, description="Items per page"),
    repo: AlertRepository = Depends(get_alert_repo)
):
    """Fetch paginated alerts."""
    offset = (page - 1) * page_size
    alerts, total_count = repo.get_alerts(
        start_date=start_date,
        end_date=end_date,
        severity=severity,
        cloud_provider=cloud_provider,
        alert_type=alert_type,
        is_resolved=is_resolved,
        limit=page_size,
        offset=offset
    )

    items = []
    for a in alerts:
        items.append(AlertListItem(
            alert_id=a.alert_id,
            alert_type=a.alert_type,
            severity=a.severity,
            cloud_provider=a.cloud_provider,
            service_category=a.service_category,
            alert_date=str(a.alert_date),
            title=a.title,
            message=a.message,
            is_resolved=a.is_resolved,
            created_at=str(a.created_at) if a.created_at else str(a.alert_date)
        ))

    return PaginatedResponse(
        data=items,
        total=total_count,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total_count
    )

@router.get("/summary", response_model=AlertSummaryResponse)
async def get_alerts_summary(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    repo: AlertRepository = Depends(get_alert_repo)
):
    """Fetch summary metrics for alerts."""
    # We can fetch all alerts in the date range quickly and process summary
    # Or just write custom queries. Since get_alerts already does basic filtering, 
    # let's write efficient queries using the DatabaseManager directly if needed, or process in memory
    
    query = "SELECT severity, alert_type, cloud_provider, is_resolved FROM alerts WHERE alert_date BETWEEN %s AND %s"
    
    total = 0
    unresolved = 0
    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    by_type = {}
    by_cloud = {}

    with DatabaseManager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (start_date, end_date))
            for row in cur.fetchall():
                sev, a_type, cloud, is_res = row
                total += 1
                if not is_res:
                    unresolved += 1
                
                if sev in by_severity:
                    by_severity[sev] += 1
                else:
                    by_severity[sev] = 1
                
                by_type[a_type] = by_type.get(a_type, 0) + 1
                by_cloud[cloud] = by_cloud.get(cloud, 0) + 1

    return AlertSummaryResponse(
        total=total,
        unresolved=unresolved,
        by_severity=by_severity,
        by_type=by_type,
        by_cloud=by_cloud
    )

@router.patch("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str = Path(..., description="Alert ID to resolve"),
    repo: AlertRepository = Depends(get_alert_repo)
):
    """Mark an alert as resolved."""
    success = repo.resolve_alert(alert_id)
    if not success:
        # Might already be resolved or not exist, we just return true anyway for idempotency 
        # or we could return 404 if it didn't exist. Let's just return true.
        pass
    return {"resolved": True, "alert_id": alert_id}
