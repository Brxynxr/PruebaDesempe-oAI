from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Definición del header requerido X-API-Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Configuración del Limiter para Rate Limiting por dirección IP
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_PER_MINUTE])

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependencia de seguridad que autentica las peticiones verificando el header X-API-Key.
    
    :param api_key: Clave enviada en las cabeceras HTTP.
    :return: Clave válida.
    :raises HTTPException: Status 401 Unauthorized si la clave es inválida o ausente.
    """
    if not api_key or api_key != settings.BACKEND_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso no autorizado: Header 'X-API-Key' ausente o inválido."
        )
    return api_key
