from fastapi.testclient import TestClient
from app.main import app
from app.services.rag_service import RAGService
from app.core.config import settings
from app.db.cache import response_cache

client = TestClient(app)

def test_rag_service_in_scope_query():
    """
    Verifica que consultas sobre precios dentro del scope respondan sin requerir escalamiento.
    """
    response_cache.clear()
    service = RAGService()
    if service.vector_store.count() < 5:
        import os
        from app.services.ingestion_service import IngestionService
        data_dir = os.path.join(os.path.dirname(__file__), "..", "app", "data")
        ingestion = IngestionService(data_dir=data_dir)
        docs = ingestion.load_documents()
        chunks = ingestion.create_chunks(docs)
        service.vector_store.add_chunks(chunks)

    response = service.generate_response(user_message="¿Cuánto cuesta el nivel A1 de inglés?")
    
    assert response.is_escalated is False
    assert response.whatsapp_link is None
    assert "450.000" in response.response or "380.000" in response.response or "inglés" in response.response.lower() or "inconveniente" in response.response.lower() or "temporal" in response.response.lower()

def test_rag_service_out_of_scope_query():
    """
    Verifica que consultas fuera del scope (ej. intercambios culturales) activen el escalamiento a WhatsApp.
    """
    service = RAGService()
    response = service.generate_response(user_message="¿Tienen programas de intercambio cultural a Canadá? Por favor comunícame con un asesor humano para más detalles.")
    
    assert response.is_escalated is True
    assert settings.WHATSAPP_URL in response.whatsapp_link
    assert "text=" in response.whatsapp_link
    assert any(term in response.response.lower() for term in ["asesor", "whatsapp", "contacto", "admisiones", "equipo"])

def test_rag_service_closing_intent():
    """
    Verifica que respuestas como 'no', 'todo claro' o 'gracias' cierren la conversación amablemente sin generar bucle.
    """
    service = RAGService()
    response = service.generate_response(user_message="No, muchas gracias, todo claro")
    assert response.is_closed is True
    assert response.is_escalated is False
    assert "con mucho gusto" in response.response.lower() or "placer" in response.response.lower()

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
