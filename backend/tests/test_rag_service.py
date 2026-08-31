from fastapi.testclient import TestClient
from app.main import app
from app.services.rag_service import RAGService
from app.core.config import settings

client = TestClient(app)

def test_rag_service_in_scope_query():
    """
    Verifica que consultas sobre precios dentro del scope respondan sin requerir escalamiento.
    """
    service = RAGService()
    response = service.generate_response(user_message="¿Cuánto cuesta el nivel A1 de inglés?")
    
    assert response.is_escalated is False
    assert response.whatsapp_link is None
    assert "450.000" in response.response or "380.000" in response.response or "inglés" in response.response.lower()

def test_rag_service_out_of_scope_query():
    """
    Verifica que consultas fuera del scope (ej. intercambios culturales) activen el escalamiento a WhatsApp.
    """
    service = RAGService()
    response = service.generate_response(user_message="¿Tienen programas de intercambio cultural a Canadá?")
    
    assert response.is_escalated is True
    assert response.whatsapp_link == settings.WHATSAPP_URL
    assert settings.WHATSAPP_URL in response.response

def test_chat_api_endpoint():
    """
    Prueba de integración del endpoint POST /api/v1/chat enviando el header X-API-Key.
    """
    headers = {"X-API-Key": settings.BACKEND_API_KEY}
    payload = {
        "message": "¿Tienen clases de francés en modalidad virtual?",
        "session_id": "test_session_123"
    }
    res = client.post("/api/v1/chat", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert data["session_id"] == "test_session_123"
    assert "is_escalated" in data
