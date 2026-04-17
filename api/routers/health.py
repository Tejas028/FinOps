from fastapi import APIRouter, Depends
from api.schemas.responses import HealthResponse
from api.dependencies import get_db
from api.config import APP_VERSION
import time

router = APIRouter()

APP_START_TIME = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check(db = Depends(get_db)):
    db_connected = db.health_check()
    status = "ok" if db_connected else "degraded"
    
    return HealthResponse(
        status=status,
        version=APP_VERSION,
        db_connected=db_connected,
        uptime_seconds=time.time() - APP_START_TIME
    )

@router.get("/ready")
async def ready_check(db = Depends(get_db)):
    if db.health_check():
        return {"ready": True}
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not reachable")
