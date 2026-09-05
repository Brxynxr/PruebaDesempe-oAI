from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse, LeadRequest
from app.services.rag_service import RAGService
from app.services.email_service import EmailService
from app.core.security import verify_api_key, limiter
from app.core.guardrails import validate_prompt_injection
from app.core.config import settings
from app.db.session import get_db
from app.db.repository import ConversationRepository
from app.services.connection_manager import manager

router = APIRouter()

# RAG service instance
rag_service = RAGService()

@router.post(
    "/chat", 
    response_model=ChatResponse, 
    summary="Process query with RAG, Groq and 4 security layers"
)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
async def handle_chat_message(
    request: Request,
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Main chat endpoint protected with 4 security levels.
    Records all interactions in SQLite database for full agent history visibility.
    """
    # Validate incoming message against Prompt Injections
    validate_prompt_injection(payload.message)
    
    # Process the query with RAG and Groq respecting requested language and conversation history
    response = rag_service.generate_response(
        user_message=payload.message,
        session_id=payload.session_id,
        language=payload.language or "en",
        history=payload.history or []
    )

    # Persist interaction into SQLite
    try:
        ConversationRepository.record_interaction(
            db=db,
            session_id=payload.session_id,
            user_message=payload.message,
            bot_response=response.response,
            is_escalated=response.is_escalated,
            idioma=payload.language or "es"
        )
    except Exception as e:
        # Logging error without breaking response flow
        pass

    # If escalated, alert agents via real-time WebSocket broadcast and async email
    if response.is_escalated:
        EmailService.send_escalation_email_async(
            user_message=payload.message,
            assistant_response=response.response,
            session_id=payload.session_id
        )
        await manager.broadcast_to_agents({
            "type": "new_escalation",
            "session_id": payload.session_id,
            "user_message": payload.message,
            "bot_response": response.response,
            "idioma": payload.language or "es"
        })

    return response

@router.post(
    "/chat/lead",
    summary="Register student lead and notify advisor via email with direct WhatsApp link"
)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def handle_lead_submission(
    request: Request,
    payload: LeadRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Endpoint to capture student contact data when personalized attention is required.
    """
    # Record lead in conversation if session exists
    try:
        conv = ConversationRepository.get_or_create_conversation(db, payload.session_id, idioma=payload.language or "es")
        ConversationRepository.add_message(
            db, 
            conv.id, 
            remitente="user", 
            contenido=f"[Lead Registrado] Nombre: {payload.name}, Tel: {payload.phone}, Programa: {payload.program}, Inquietud: {payload.user_message}"
        )
        conv.estado = "pendiente"
        db.commit()
    except Exception:
        pass

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

