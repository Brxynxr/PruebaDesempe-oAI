from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Required X-API-Key header specification
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Limiter configuration for per-IP rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_PER_MINUTE])

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Security dependency authenticating incoming requests via X-API-Key header.
    
    :param api_key: Key provided in HTTP header.
    :return: Validated key string.
    :raises HTTPException: Status 401 Unauthorized if key is missing or invalid.
    """
    if not api_key or api_key != settings.BACKEND_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid 'X-API-Key' header."
        )
    return api_key
