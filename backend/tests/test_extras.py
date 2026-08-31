from fastapi.testclient import TestClient
from app.main import app
from app.db.cache import ResponseCache
from app.schemas.chat import ChatResponse
from app.core.config import settings

client = TestClient(app)
VALID_HEADERS = {"X-API-Key": settings.BACKEND_API_KEY}

def test_response_cache_hit_and_miss():
    """
    Verifies cache miss and hit behaviors on TTL response store.
    """
    cache = ResponseCache(ttl_seconds=10)
    query = "¿Cuánto cuesta la matrícula?"
    
    # 1. Cache Miss
    assert cache.get(query) is None
    
    # 2. Cache Set & Hit
    dummy_resp = ChatResponse(
        response="La matrícula cuesta $450.000 COP presencial.",
        is_escalated=False,
        session_id="s1"
    )
    cache.set(query, dummy_resp)
    
    cached = cache.get(query)
    assert cached is not None
    assert cached.response == dummy_resp.response

def test_metrics_endpoint():
    """
    Verifies GET /api/v1/metrics endpoint requires authentication and returns analytics metrics.
    """
    # 1. Unauthenticated -> 401 Unauthorized
    res_unauth = client.get("/api/v1/metrics")
    assert res_unauth.status_code == 401
    
    # 2. Authenticated -> 200 OK
    res = client.get("/api/v1/metrics", headers=VALID_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "total_queries" in data
    assert "escalation_rate_percentage" in data
    assert "cache_hit_rate_percentage" in data
    assert "estimated_cost_usd" in data
