import re
from fastapi import HTTPException, status

# Patrones comunes utilizados en ataques de prompt injection
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an)?",
    r"do\s+anything\s+now",
    r"jailbreak",
    r"ignore\s+above",
    r"override\s+(the\s+)?system",
    r"revela\s+(el\s+)?prompt",
    r"ignora\s+(las\s+)?instrucciones",
    r"olvida\s+(las\s+)?instrucciones",
    r"ahora\s+eres\s+un",
]

def validate_prompt_injection(message: str) -> None:
    """
    Valida el mensaje del usuario frente a patrones conocidos de Prompt Injection.
    Si se detecta una amenaza, interrumpe el procesamiento lanzando una excepción HTTP 400.
    
    :param message: Texto enviado por el usuario.
    :raises HTTPException: Si el mensaje contiene un intento de prompt injection.
    """
    clean_message = message.lower()
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, clean_message):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solicitud rechazada por políticas de seguridad (intento de manipulación de prompt detectado)."
            )
