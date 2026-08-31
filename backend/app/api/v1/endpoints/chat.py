from fastapi import APIRouter, Depends, Request
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.core.security import verify_api_key, limiter
from app.core.guardrails import validate_prompt_injection
from app.core.config import settings

router = APIRouter()

# RAG service singleton instance
rag_service = RAGService()

@router.post(
    "/chat", 
    response_model=ChatResponse, 
    summary="Process customer inquiry with RAG, Groq, and 4 security layers"
)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def handle_chat_message(
    request: Request,
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key)
) -> ChatResponse:
    """
    Main chat endpoint protected with 4 security layers:
    1. Per-IP Rate Limiting (10 req/min via SlowAPI)
    2. Header Authentication (X-API-Key requirement)
    3. Anti Prompt-Injection Guardrails (Jailbreak pattern filter)
    4. Secure Environment Secret Management (.env)
    """
    # Validate incoming message against Prompt Injection threats
    validate_prompt_injection(payload.message)
    
    # Process query through RAG pipeline and Groq synthesis
    return rag_service.generate_response(
        user_message=payload.message,
        session_id=payload.session_id
    )
