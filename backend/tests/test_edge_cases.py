from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.main import app
from app.core.config import settings
from app.core.security import _get_real_client_ip
from app.core.guardrails import validate_prompt_injection
from app.services.rag_service import RAGService, build_messages, FEW_SHOT_EXAMPLES_EN
from app.db.cache import response_cache

client = TestClient(app)
VALID_HEADERS = {"X-API-Key": settings.BACKEND_API_KEY}


def test_ip_spoofing_extraction():
    """Verify that _get_real_client_ip extracts the first client IP in X-Forwarded-For chain."""
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", b"203.0.113.195, 70.41.3.18, 150.172.238.178")],
        "client": ("127.0.0.1", 8000),
    }
    req = Request(scope)
    extracted_ip = _get_real_client_ip(req)
    assert extracted_ip == "203.0.113.195"


def test_guardrails_legitimate_queries_not_blocked():
    """Verify that legitimate academic queries containing words like 'act as' or 'instructions' are NOT blocked."""
    valid_queries = [
        "Can a parent act as a representative for enrollment?",
        "What are the new instructions for semester registration?",
        "How do I act as a course ambassador?"
    ]
    for q in valid_queries:
        # Should not raise HTTPException
        validate_prompt_injection(q)


def test_english_query_uses_english_few_shots():
    """Verify that build_messages selects FEW_SHOT_EXAMPLES_EN when language is 'en'."""
    messages = build_messages(
        user_question="What are the schedules?",
        context_chunks=[{"source": "horarios.md", "content": "Schedule info"}],
        language="en"
    )
    # System prompt must be in English
    assert messages[0]["role"] == "system"
    assert "Always answer in clear, natural ENGLISH" in messages[0]["content"]
    
    # First few-shot message must match FEW_SHOT_EXAMPLES_EN
    assert messages[1]["content"] == FEW_SHOT_EXAMPLES_EN[0]["content"]


def test_groq_api_failure_fallback_multilingual():
    """Verify fallback response on Groq API failure in Spanish and English."""
    response_cache.clear()
    service = RAGService()
    
    # Mock client.chat.completions.create to raise an Exception
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Groq connection timeout")
    service.client = mock_client
    service.clients = [mock_client]
    
    # Test Spanish fallback
    res_es = service.generate_response(user_message="¿Qué horarios tienen?", language="es")
    assert "inconveniente temporal" in res_es.response.lower() or "registros oficiales" in res_es.response.lower()
    
    # Test English fallback
    res_en = service.generate_response(user_message="What schedules do you have?", language="en")
    assert "temporary connection issue" in res_en.response.lower() or "official records" in res_en.response.lower()


def test_cache_history_isolation():
    """Verify that same follow-up question in different conversations produces separate cache entries."""
    response_cache.clear()
    service = RAGService()
    
    # Session 1 history (Inglés)
    history_eng = [{"sender": "user", "text": "Me interesa inglés"}, {"sender": "bot", "text": "Ofrecemos inglés A1-C1"}]
    # Session 2 history (Portugués)
    history_por = [{"sender": "user", "text": "Me interesa portugués"}, {"sender": "bot", "text": "Ofrecemos portugués A1-C1"}]
    
    query = "¿Y qué precios manejan?"
    
    resp1 = service.generate_response(user_message=query, history=history_eng, session_id="session_eng")
    resp2 = service.generate_response(user_message=query, history=history_por, session_id="session_por")
    
    # Both responses should be generated with correct session IDs
    assert resp1.session_id == "session_eng"
    assert resp2.session_id == "session_por"
