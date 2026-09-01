import time
from app.db.cache import ResponseCache
from app.schemas.chat import ChatResponse

def test_cache_hit_and_miss():
    """
    Verify basic cache storage, retrieval, and cache miss behavior.
    """
    cache = ResponseCache(ttl_seconds=5)
    
    # 1. Cache Miss
    assert cache.get("¿Cuánto cuesta el curso?") is None

    # 2. Store item
    sample_response = ChatResponse(
        response="El curso cuesta $450.000 COP.",
        is_escalated=False,
        is_closed=False,
        session_id="cache_session_01"
    )
    cache.set("¿Cuánto cuesta el curso?", sample_response)

    # 3. Cache Hit (with case insensitivity and whitespace normalization)
    hit_resp = cache.get("  ¿cuánto Cuesta el curso?  ")
    assert hit_resp is not None
    assert hit_resp.response == "El curso cuesta $450.000 COP."

def test_cache_ttl_expiration():
    """
    Verify that cache entries expire after the configured TTL.
    """
    cache = ResponseCache(ttl_seconds=1)
    sample_response = ChatResponse(
        response="Test expired response",
        is_escalated=False,
        is_closed=False,
        session_id="ttl_session"
    )
    cache.set("pregunta temporal", sample_response)
    
    # Immediately available
    assert cache.get("pregunta temporal") is not None

    # After 1.1s, it must expire
    time.sleep(1.1)
    assert cache.get("pregunta temporal") is None

def test_cache_clear():
    """
    Verify complete cache clearing functionality.
    """
    cache = ResponseCache(ttl_seconds=60)
    sample = ChatResponse(
        response="Respuesta",
        is_escalated=False,
        is_closed=False,
        session_id="s1"
    )
    cache.set("q1", sample)
    cache.set("q2", sample)
    
    cache.clear()
    assert cache.get("q1") is None
    assert cache.get("q2") is None
