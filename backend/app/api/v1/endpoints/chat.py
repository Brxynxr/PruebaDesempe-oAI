import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.schemas.chat import ChatRequest, ChatResponse, LeadRequest
from app.services.rag_service import RAGService
from app.services.telegram_service import TelegramService
from app.core.security import verify_api_key, limiter
from app.core.guardrails import validate_prompt_injection
from app.core.config import settings
from app.db.session import get_db
from app.db.repository import ConversationRepository
from app.services.connection_manager import manager

logger = logging.getLogger("lumina.chat")

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
            is_escalated=False,  # Keep state as 'bot' in DB until student confirms handoff / submits lead
            idioma=payload.language or "es"
        )
    except Exception as e:
        logger.error("Error al persistir interacción de chat: %s", str(e), exc_info=True)

    return response

@router.post(
    "/chat/lead",
    summary="Register student lead and notify advisor via email/telegram with direct WhatsApp link"
)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
async def handle_lead_submission(
    request: Request,
    payload: LeadRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Endpoint to capture student contact data when personalized attention is required.
    Transitions conversation to 'pendiente' and alerts advisors via Telegram, Email, and WebSockets.
    """
    # Record lead in conversation if session exists
    try:
        conv = ConversationRepository.get_or_create_conversation(db, payload.session_id, idioma=payload.language or "es")
        ConversationRepository.add_message(
            db, 
            conv.id, 
            remitente="system", 
            contenido=f"Lead de contacto registrado: {payload.name} (Tel: {payload.phone}, Programa: {payload.program})"
        )
        conv.estado = "pendiente"
        db.commit()
    except Exception as e:
        logger.error("Error al registrar lead en la base de datos: %s", str(e), exc_info=True)

    TelegramService.send_lead_alert(
        student_name=payload.name,
        student_phone=payload.phone,
        program=payload.program,
        user_message=payload.user_message,
        session_id=payload.session_id
    )
    await manager.broadcast_to_agents({
        "type": "new_escalation",
        "session_id": payload.session_id,
        "user_message": f"Lead: {payload.name} ({payload.phone}) - {payload.user_message}",
        "bot_response": "Esperando atención de asesor...",
        "idioma": payload.language or "es"
    })
    return {
        "status": "success",
        "message": f"¡Gracias, {payload.name}! En unos instantes un asesor te atenderá por este chat."
    }

