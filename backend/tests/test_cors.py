from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_allowed_origin():
    """
    Verify that requests from allowed origins receive Access-Control-Allow-Origin header.
    """
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,X-API-Key"
    }
    res = client.options("/api/v1/chat", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"

def test_cors_disallowed_origin():
    """
    Verify that requests from unauthorized origins do not receive Access-Control-Allow-Origin header.
    """
    headers = {
        "Origin": "http://malicious-untrusted-site.com",
        "Access-Control-Request-Method": "POST"
    }
    res = client.options("/api/v1/chat", headers=headers)
    assert res.headers.get("access-control-allow-origin") is None
