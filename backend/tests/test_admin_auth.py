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

def test_cannot_send_message_without_claiming():
    """
    Verifica que no se puedan enviar mensajes en una conversación 'pendiente' sin antes tomar el caso.
    """
    from app.db.session import SessionLocal
    from app.db.repository import ConversationRepository
    
    db = SessionLocal()
    try:
        conv = ConversationRepository.create_custom_conversation(
            db,
            session_id="test_unclaimed_session_guard",
            idioma="es",
            estado="pendiente",
            initial_message="Mensaje inicial de prueba para guard"
        )
        conv_id = conv.id

        # 1. Login to get token
        login_res = client.post("/api/v1/admin/login", json={
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Attempt to send a message without claiming (should return 400 Bad Request)
        res = client.post(
            f"/api/v1/admin/conversations/{conv_id}/messages",
            json={"message": "Intento de envío sin tomar caso"},
            headers=headers
        )
        assert res.status_code == 400
        assert "tomar el caso" in res.json()["detail"].lower()

        # 3. Claim the case
        claim_res = client.post(
            f"/api/v1/admin/conversations/{conv_id}/claim",
            headers=headers
        )
        assert claim_res.status_code == 200
        assert claim_res.json()["estado"] == "en_atencion"

        # 4. Now sending a message succeeds
        msg_res = client.post(
            f"/api/v1/admin/conversations/{conv_id}/messages",
            json={"message": "Hola, ya tomé tu caso y respondo con éxito"},
            headers=headers
        )
        assert msg_res.status_code == 200
        assert msg_res.json()["status"] == "sent"

        # Clean up
        ConversationRepository.delete_conversation(db, conv_id)
    finally:
        db.close()
