from fastapi import APIRouter, Depends, Request
from app.schemas.chat import ChatRequest, ChatResponse, LeadRequest
from app.services.rag_service import RAGService
from app.services.email_service import EmailService
from app.core.security import verify_api_key, limiter
from app.core.guardrails import validate_prompt_injection
from app.core.config import settings

router = APIRouter()

# RAG service instance
rag_service = RAGService()

@router.post(
    "/chat", 
    response_model=ChatResponse, 
    summary="Process query with RAG, Groq and 4 security layers"
)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def handle_chat_message(
    request: Request,
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key)
) -> ChatResponse:
    """
    Main chat endpoint protected with 4 security levels.
    """
    # Validate incoming message against Prompt Injections
    validate_prompt_injection(payload.message)
    
    # Process the query with RAG and Groq respecting the requested language and conversation history
    return rag_service.generate_response(
        user_message=payload.message,
        session_id=payload.session_id,
        language=payload.language or "en",
        history=payload.history or []
    )

@router.post(
    "/chat/lead",
    summary="Register student lead and notify advisor via email with direct WhatsApp link"
)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def handle_lead_submission(
    request: Request,
    payload: LeadRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Endpoint to capture student contact data when personalized attention is required.
    """
    EmailService.send_lead_email_async(
        student_name=payload.name,
        student_phone=payload.phone,
        program=payload.program,
        user_message=payload.user_message,
        session_id=payload.session_id
    )
    return {
        "status": "success",
        "message": f"Thank you {payload.name}! Your details have been sent to an Academia Lumina advisor. We will contact you via WhatsApp shortly."
    }
