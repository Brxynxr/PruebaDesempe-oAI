import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_rate_limiting_enforced():
    """
    Verify that excessive requests from the same client IP trigger HTTP 429 Too Many Requests.
    """
    headers = {
        "X-API-Key": settings.BACKEND_API_KEY,
        "X-Forwarded-For": "198.51.100.42"
    }
    payload = {
        "message": "Hola, ¿tienen cursos de inglés?",
        "session_id": "test_rate_session"
    }

    # First request should succeed
    res = client.post("/api/v1/chat", json=payload, headers=headers)
    assert res.status_code == 200

    # Flood requests to exceed rate limit (configured as 10/minute)
    exceeded = False
    for _ in range(15):
        res = client.post("/api/v1/chat", json=payload, headers=headers)
        if res.status_code == 429:
            exceeded = True
            break
            
    assert exceeded is True, "Rate limit should return HTTP 429 when threshold is exceeded"
