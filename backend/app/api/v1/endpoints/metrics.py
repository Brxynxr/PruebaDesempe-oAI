from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.metrics_service import metrics_service
from app.core.security import verify_api_key

router = APIRouter()

@router.get(
    "/metrics", 
    summary="Get operational metrics and customer service analytics",
    dependencies=[Depends(verify_api_key)]
)
def get_metrics() -> Dict[str, Any]:
    """
    Returns detailed system analytics:
    - Total processed queries.
    - Queries served from cache (cache hit rate).
    - Queries escalated to advisor via WhatsApp (escalation rate).
    - Estimated tokens consumed and estimated cost ($ USD).
    """
    return metrics_service.get_metrics_summary()
