from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.metrics_service import metrics_service
from app.core.security import verify_api_key

router = APIRouter()

@router.get(
    "/metrics", 
    summary="Get operational metrics and customer support statistics",
    dependencies=[Depends(verify_api_key)]
)
def get_metrics() -> Dict[str, Any]:
    """
    Returns detailed system analytics:
    - Total queries processed.
    - Queries served from cache (cache hit rate).
    - Queries escalated to human support via WhatsApp (escalation rate).
    - Estimated token consumption and cost ($ USD).
    """
    return metrics_service.get_metrics_summary()
