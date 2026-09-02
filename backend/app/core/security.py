import ipaddress
from fastapi import Security, HTTPException, status, Request
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def _get_real_client_ip(request: Request) -> str:
    """
    Extract real client IP safely by taking the first IP address from the X-Forwarded-For header chain.
    Validates format to prevent IP spoofing attacks.
    Note: Assumes Render (or equivalent upstream reverse proxy) acts as the trusted entry gateway
    that correctly prepends or sets the client's origin IP.
    """
    # 1. Check X-Forwarded-For header (first IP in the proxy chain is the client origin)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        raw_ip = forwarded_for.split(",")[0].strip()
        try:
            ipaddress.ip_address(raw_ip)
            return raw_ip
        except ValueError:
            pass

    # 2. Check X-Real-IP header as fallback
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        clean_ip = real_ip.strip()
        try:
            ipaddress.ip_address(clean_ip)
            return clean_ip
        except ValueError:
            pass

    # 3. Direct client connection host fallback
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
