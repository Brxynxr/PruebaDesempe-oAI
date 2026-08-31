from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.metrics_service import metrics_service
from app.core.security import verify_api_key

router = APIRouter()

@router.get(
    "/metrics", 
    summary="Obtener métricas y estadísticas operativas de atención al cliente",
    dependencies=[Depends(verify_api_key)]
)
def get_metrics() -> Dict[str, Any]:
    """
    Retorna analítica detallada del sistema:
    - Total de consultas procesadas.
    - Consultas atendidas desde la caché (cache hit rate).
    - Consultas escaladas a asesor por WhatsApp (escalation rate).
    - Tokens estimados consumidos y costo estimado ($ USD).
    """
    return metrics_service.get_metrics_summary()
