import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.metrics_service import MetricsService

client = TestClient(app)

def test_metrics_service_token_and_cost_calculation():
    service = MetricsService()
    
    # Initial state
    summary = service.get_metrics_summary()
    assert summary["total_tokens"] == 0

    # Record real queries with exact tokens
    service.record_query(is_cached=False, is_escalated=False, tokens=150)
    service.record_query(is_cached=True, is_escalated=False, tokens=0)
    service.record_query(is_cached=False, is_escalated=True, tokens=350)

    summary = service.get_metrics_summary()
    assert summary["total_queries"] == 3
    assert summary["cached_queries"] == 1
    assert summary["escalated_queries"] == 1
    assert summary["total_tokens"] == 500
    assert summary["cache_hit_rate_percentage"] == "33.33%"
    assert summary["escalation_rate_percentage"] == "33.33%"
    assert "estimated_cost_usd" in summary

def test_metrics_endpoint_with_admin_bearer_token():
    # Login as admin
    login_res = client.post("/api/v1/admin/login", json={
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD
    })
    token = login_res.json()["access_token"]
    
    # Request metrics with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_queries" in data
    assert "total_tokens" in data
    assert "estimated_cost_usd" in data
    assert "cache_hit_rate_percentage" in data
