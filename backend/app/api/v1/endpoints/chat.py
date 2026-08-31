from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Procesar consulta de atención al cliente")
def handle_chat_message(request: ChatRequest) -> ChatResponse:
    """
    Endpoint base para procesamiento de consultas (se integrará con RAG y Groq en Fase 3).
    """
    # Respuesta base placeholder para verificar la conectividad de la Fase 1
    return ChatResponse(
        response="¡Hola! Soy el asistente de Academia Lumina. El backend base está activo.",
        is_escalated=False,
        session_id=request.session_id,
        sources=[]
    )
