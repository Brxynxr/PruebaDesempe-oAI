from fastapi import Security, HTTPException, status, Request
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def _get_real_client_ip(request: Request) -> str:
    """Extract real client IP from X-Forwarded-For header when behind a reverse proxy."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

limiter = Limiter(key_func=_get_real_client_ip, default_limits=[settings.RATE_LIMIT_PER_MINUTE])

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Authenticate incoming requests via X-API-Key header."""
    if not api_key or api_key != settings.BACKEND_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: missing or invalid 'X-API-Key' header."
        )
    return api_key
