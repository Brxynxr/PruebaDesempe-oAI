from fastapi import APIRouter
from app.schemas.chat import HealthResponse
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse, summary="Check API health status")
def get_health_status() -> HealthResponse:
    """
    Health check endpoint for monitoring and deployment verification.
    """
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )
