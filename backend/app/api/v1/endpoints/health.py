from fastapi import APIRouter
from app.schemas.chat import HealthResponse
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse, summary="Verify system health status")
def get_health_status() -> HealthResponse:
    """
    Health check endpoint for deployment monitoring and verification.
    """
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )
