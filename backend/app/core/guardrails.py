import re
import unicodedata
from fastapi import HTTPException, status

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an)?",
    r"do\s+anything\s+now",
    r"jailbreak",
    r"ignore\s+above",
    r"override\s+(the\s+)?system",
    r"reveal\s+(the\s+)?prompt",
    r"revela\s+(el\s+)?prompt",
    r"ignora\s+(las\s+)?instrucciones",
    r"olvida\s+(las\s+)?instrucciones",
    r"ahora\s+eres\s+un",
    r"pretend\s+you",
    r"bypass\s+(all\s+)?filter",
    r"disregard\s+(all\s+)?(previous|prior)",
    r"new\s+instructions",
    r"repeat\s+after\s+me",
]

def _normalize_text(text: str) -> str:
    """Normalize unicode, strip accents, and collapse whitespace for robust pattern matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    collapsed = re.sub(r"[.\-_/\\]", "", stripped)
    return collapsed.lower()

def validate_prompt_injection(message: str) -> None:
    """Validate user message against known prompt injection patterns.
    Raises HTTP 400 if a potential injection attack is detected."""
    normalized = _normalize_text(message)
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request rejected: potential prompt manipulation detected."
            )
