from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.metrics_service import MetricsService

client = TestClient(app)

def test_metrics_service_calculation():
    """
    Verify internal MetricsService rate calculations and token tracking.
    """
    service = MetricsService()
    
    # Initial state
    summary = service.get_metrics_summary()
    assert summary["total_queries"] == 0
    assert summary["cache_hit_rate_percentage"] == "0.0%"
    assert summary["escalation_rate_percentage"] == "0.0%"

    # Record queries
    service.record_query(is_cached=True, is_escalated=False, tokens=100)
    service.record_query(is_cached=False, is_escalated=True, tokens=200)
    
    summary2 = service.get_metrics_summary()
    assert summary2["total_queries"] == 2
    assert summary2["cached_queries"] == 1
    assert summary2["escalated_queries"] == 1
    assert summary2["cache_hit_rate_percentage"] == "50.0%"
    assert summary2["escalation_rate_percentage"] == "50.0%"
    assert summary2["total_tokens_estimated"] == 300

def test_metrics_endpoint_authorized():
    """
    Verify GET /api/v1/metrics returns HTTP 200 with valid X-API-Key.
    """
    headers = {"X-API-Key": settings.BACKEND_API_KEY}
    res = client.get("/api/v1/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_queries" in data
    assert "cache_hit_rate_percentage" in data
    assert "escalation_rate_percentage" in data

def test_metrics_endpoint_unauthorized():
    """
    Verify GET /api/v1/metrics returns HTTP 401 without API key.
    """
    res = client.get("/api/v1/metrics")
    assert res.status_code == 401
