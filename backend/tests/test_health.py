from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """
    Verifies root endpoint returns 200 OK and welcome message.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_check_endpoint():
    """
    Verifies health check endpoint /api/v1/health returns status 'ok'.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
