import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.repository import ConversationRepository
from app.db.models import Conversation, Message

client = TestClient(app)

def get_admin_auth_headers():
    login_res = client.post("/api/v1/admin/login", json={
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_conversation_lifecycle_and_state_transitions():
    db = SessionLocal()
    try:
        session_id = f"test_lifecycle_{int(datetime.now(timezone.utc).timestamp())}"
        
        # 1. Initial State: bot
        conv = ConversationRepository.get_or_create_conversation(db, session_id=session_id)
        conv_id = conv.id
        assert conv.estado == "bot"
        assert conv.session_id == session_id

        # 2. Add user and bot messages
        msg1 = ConversationRepository.add_message(db, conversation_id=conv_id, remitente="user", contenido="Hola, necesito información")
        msg2 = ConversationRepository.add_message(db, conversation_id=conv_id, remitente="bot", contenido="¡Hola! Te puedo ayudar con precios...")
        assert msg1.remitente == "user"
        assert msg2.remitente == "bot"

        # 3. Transition to 'pendiente' (escalation)
        conv.estado = "pendiente"
        db.commit()
        db.refresh(conv)
        assert conv.estado == "pendiente"

        # 4. Advisor claims conversation -> 'en_atencion'
        conv_claimed = ConversationRepository.claim_conversation(db, conversation_id=conv_id, agent_username="asesor_ana")
        assert conv_claimed.estado == "en_atencion"
        assert conv_claimed.agente_asignado == "asesor_ana"

        # 5. Advisor sends message
        msg_agent = ConversationRepository.add_message(db, conversation_id=conv_id, remitente="agent", contenido="Hola, soy Ana, tu asesora.")
        assert msg_agent.remitente == "agent"

        # 6. Advisor resolves conversation -> 'resuelto'
        conv_resolved = ConversationRepository.resolve_conversation(db, conversation_id=conv_id)
        assert conv_resolved.estado == "resuelto"
    finally:
        db.close()

def test_admin_conversations_api_flow():
    headers = get_admin_auth_headers()
    session_id = f"test_api_flow_{int(datetime.now(timezone.utc).timestamp())}"

    # Setup conversation in DB
    db = SessionLocal()
    try:
        conv = ConversationRepository.get_or_create_conversation(db, session_id=session_id)
        conv.estado = "pendiente"
        db.commit()
        conv_id = conv.id
        ConversationRepository.add_message(db, conversation_id=conv_id, remitente="user", contenido="Consulta de prueba")
    finally:
        db.close()

    # List conversations via Admin API
    res = client.get("/api/v1/admin/conversations?estado=pendiente", headers=headers)
    assert res.status_code == 200
    convs = res.json()
    assert any(c["session_id"] == session_id for c in convs)

    # Claim conversation via Admin API
    claim_res = client.post(f"/api/v1/admin/conversations/{conv_id}/claim", headers=headers)
    assert claim_res.status_code == 200
    assert claim_res.json()["estado"] == "en_atencion"
    assert claim_res.json()["agente_asignado"] == settings.ADMIN_USERNAME

    # Resolve conversation via Admin API
    resolve_res = client.post(f"/api/v1/admin/conversations/{conv_id}/resolve", headers=headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["estado"] == "resuelto"

def test_sla_breach_detection():
    db = SessionLocal()
    try:
        old_session_id = f"test_sla_breach_{int(datetime.now(timezone.utc).timestamp())}"
        conv = ConversationRepository.get_or_create_conversation(db, session_id=old_session_id)
        conv.estado = "pendiente"
        # Set updated_at to 15 minutes ago
        conv.updated_at = datetime.now(timezone.utc) - timedelta(minutes=15)
        db.commit()

        # Check breach with 10 min threshold
        breached = ConversationRepository.get_sla_breached_conversations(db, threshold_minutes=10)
        assert any(c.session_id == old_session_id for c in breached)
    finally:
        db.close()

def test_cleanup_resolved_conversations_after_30_minutes():
    db = SessionLocal()
    try:
        # Case 1: Resolved 40 minutes ago (should be pruned)
        old_session = f"test_resolved_old_{int(datetime.now(timezone.utc).timestamp())}"
        conv_old = ConversationRepository.get_or_create_conversation(db, session_id=old_session)
        conv_old.estado = "resuelto"
        conv_old.updated_at = datetime.now(timezone.utc) - timedelta(minutes=40)
        ConversationRepository.add_message(db, conv_old.id, remitente="user", contenido="Mensaje antiguo")
        db.commit()

        # Case 2: Resolved 5 minutes ago (should NOT be pruned)
        recent_session = f"test_resolved_recent_{int(datetime.now(timezone.utc).timestamp())}"
        conv_recent = ConversationRepository.get_or_create_conversation(db, session_id=recent_session)
        conv_recent.estado = "resuelto"
        conv_recent.updated_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        ConversationRepository.add_message(db, conv_recent.id, remitente="user", contenido="Mensaje reciente")
        db.commit()

        # Run cleanup with 30 min threshold
        deleted_count = ConversationRepository.cleanup_old_resolved_conversations(db, max_age_minutes=30)
        assert deleted_count >= 1

        # Verify old resolved conversation is gone
        assert ConversationRepository.get_conversation_by_session_id(db, old_session) is None
        # Verify recent resolved conversation is still preserved
        assert ConversationRepository.get_conversation_by_session_id(db, recent_session) is not None
    finally:
        db.close()
