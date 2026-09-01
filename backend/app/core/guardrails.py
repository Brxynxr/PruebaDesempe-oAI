import re
import unicodedata
from fastapi import HTTPException, status

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above|system|existing)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior|system)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|system|above|constraints)",
    r"system\s+(prompt|instructions|directive|message|rules)",
    r"reveal\s+(the\s+)?(system\s+)?prompt",
    r"revela\s+(el\s+)?(system\s+)?prompt",
    r"show\s+(me\s+)?(the\s+)?(system\s+)?prompt",
    r"muestra\s+(el\s+)?(prompt|sistema)",
    r"output\s+(your\s+)?(initial|system)\s+prompt",
    r"you\s+are\s+now\s+(a|an|in)",
    r"act\s+as\s+(a|an|if)?",
    r"do\s+anything\s+now",
    r"dan\s+mode",
    r"jailbreak",
    r"ignore\s+above",
    r"override\s+(the\s+)?system",
    r"ignora\s+(todas\s+las\s+|las\s+)?instrucciones",
    r"olvida\s+(todas\s+las\s+|las\s+)?instrucciones",
    r"ahora\s+eres\s+(un|una)?",
    r"pretend\s+you(\s+are)?",
    r"bypass\s+(all\s+)?(filter|security|safety)",
    r"new\s+instructions",
    r"repeat\s+after\s+me",
]

# Character mappings to neutralize leetspeak evasion attempts
LEET_MAP = {
    '0': 'o',
    '1': 'i',
    '!': 'i',
    '|': 'i',
    '3': 'e',
    '4': 'a',
    '@': 'a',
    '5': 's',
    '$': 's',
    '7': 't',
}

def _normalize_text(text: str) -> str:
    """
    Normalize unicode, strip accents, translate leetspeak, and collapse whitespace
    for robust pattern matching against evasive prompt injection attempts.
    """
    if not text:
        return ""
        
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c)).lower()
    
    # Translate leetspeak characters
    leet_translated = "".join(LEET_MAP.get(c, c) for c in stripped)
    
    # Remove markdown delimiters, code fences, backticks, and punctuation
    cleaned = re.sub(r"[`*_\-#\/\\\[\]\(\)\{\}:;\"']", " ", leet_translated)
    
    # Collapse multiple whitespaces into a single space
    collapsed = re.sub(r"\s+", " ", cleaned).strip()
    return collapsed

def validate_prompt_injection(message: str) -> None:
    """
    Validate user message against known prompt injection patterns.
    Raises HTTP 400 Bad Request if a potential injection attack is detected.
    """
    normalized = _normalize_text(message)
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request rejected: potential prompt manipulation detected."
            )
