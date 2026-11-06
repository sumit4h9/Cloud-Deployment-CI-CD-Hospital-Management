from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["Health & Readiness"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Liveness probe: verifies service process is running."""
    return HealthResponse(
        status="healthy",
        service="doctor-appointment-api",
        version="1.0.0"
    )

@router.get("/ready", response_model=ReadyResponse)
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe: verifies service dependencies (database) are operational."""
    try:
        db.execute(text("SELECT 1"))
        return ReadyResponse(
            status="ready",
            database="connected"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database readiness failed: {str(e)}"
        )
