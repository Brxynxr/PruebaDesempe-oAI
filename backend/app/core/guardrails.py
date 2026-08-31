import re
from fastapi import HTTPException, status

# Common regex patterns used in Prompt Injection / Jailbreak attacks
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
    Validates user input against known Prompt Injection patterns.
    If a potential threat is detected, halts execution with an HTTP 400 Exception.
    
    :param message: Raw text message sent by user.
    :raises HTTPException: Status 400 Bad Request if prompt injection is detected.
    """
    clean_message = message.lower()
    
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, clean_message):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request rejected due to security policy (Prompt Injection attempt detected)."
            )
