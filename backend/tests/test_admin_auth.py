import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.auth import verify_password, hash_password, create_access_token

client = TestClient(app)

def test_password_hashing_and_verification():
    password = "secret_password_2026"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_admin_login_success():
    payload = {
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD
    }
    res = client.post("/api/v1/admin/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == settings.ADMIN_USERNAME

def test_admin_login_invalid_password():
    payload = {
        "username": settings.ADMIN_USERNAME,
        "password": "wrongpassword123"
    }
    res = client.post("/api/v1/admin/login", json=payload)
    assert res.status_code == 401
    data = res.json()
    assert "detail" in data

def test_admin_login_invalid_username():
    payload = {
        "username": "non_existent_user_999",
        "password": settings.ADMIN_PASSWORD
    }
    res = client.post("/api/v1/admin/login", json=payload)
    assert res.status_code == 401

def test_admin_me_endpoint_with_valid_token():
    # 1. Login to get token
    login_res = client.post("/api/v1/admin/login", json={
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD
    })
    token = login_res.json()["access_token"]
    
    # 2. Access /admin/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/admin/me", headers=headers)
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["username"] == settings.ADMIN_USERNAME

def test_admin_me_endpoint_unauthorized():
    res = client.get("/api/v1/admin/me")
    assert res.status_code == 401

    res_invalid = client.get("/api/v1/admin/me", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert res_invalid.status_code == 401
