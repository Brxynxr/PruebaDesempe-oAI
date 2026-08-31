from fastapi import APIRouter
from app.schemas.chat import HealthResponse
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse, summary="Verificar el estado de salud de la API")
def get_health_status() -> HealthResponse:
    """
    Endpoint de comprobación de estado para monitoreo y verificación de despliegue.
    """
    return HealthResponse(
        status="ok",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )
