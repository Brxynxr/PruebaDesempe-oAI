from fastapi import APIRouter, Request, HTTPException, status, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repository import ConversationRepository
from app.services.metrics_service import metrics_service
from app.core.config import settings
from app.core.auth import decode_access_token

router = APIRouter()

@router.get(
    "/metrics", 
    summary="Get operational metrics and customer service analytics"
)
def get_metrics(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns detailed system analytics authenticated via Admin JWT token or X-API-Key:
    - Total processed queries & AI autonomous resolution rate.
    - Queries served from cache (cache hit rate & token savings).
    - Queries escalated (escalation rate).
    - Real tokens consumed and estimated costs ($ USD).
    - Database conversation lifecycle metrics (pendientes, en atención, resueltos).
    """
    db_stats = ConversationRepository.get_conversation_stats(db)

    # 1. Validate X-API-Key
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key == settings.BACKEND_API_KEY:
        return metrics_service.get_metrics_summary(db_stats=db_stats)

    # 2. Validate Bearer JWT token from Admin panel
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            decode_access_token(token)
            return metrics_service.get_metrics_summary(db_stats=db_stats)
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Valid 'Authorization: Bearer <token>' or 'X-API-Key' header required."
    )

