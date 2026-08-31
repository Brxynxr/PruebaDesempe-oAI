from fastapi import APIRouter, Depends, Request
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.core.security import verify_api_key, limiter
from app.core.guardrails import validate_prompt_injection
from app.core.config import settings

router = APIRouter()

# Instancia del servicio RAG
rag_service = RAGService()

@router.post(
    "/chat", 
    response_model=ChatResponse, 
    summary="Procesar consulta con RAG, Groq y seguridad integrada"
)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def handle_chat_message(
    request: Request,
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key)
) -> ChatResponse:
    """
    Endpoint principal de chat protegido con 4 niveles de seguridad:
    1. Rate limiting (10 req/min por IP via slowapi)
    2. Autenticación por header X-API-Key
    3. Validación Anti-Prompt Injection (bloqueo de intentos de jailbreak)
    4. Gestión segura de secretos vía .env
    """
    # Validar el mensaje de entrada frente a Prompt Injections
    validate_prompt_injection(payload.message)
    
    # Procesar la consulta con RAG y Groq
    return rag_service.generate_response(
        user_message=payload.message,
        session_id=payload.session_id
    )
