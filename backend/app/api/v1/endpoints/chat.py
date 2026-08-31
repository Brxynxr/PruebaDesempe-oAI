from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter()

# Instancia global del servicio RAG
rag_service = RAGService()

@router.post("/chat", response_model=ChatResponse, summary="Procesar consulta de atención al cliente con RAG y Groq")
def handle_chat_message(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal de chat.
    Recibe la pregunta del usuario o de n8n, realiza la búsqueda semántica en la base vectorial,
    sintetiza la respuesta con Llama 3.3 70B de Groq y detecta necesidad de escalamiento a WhatsApp.
    """
    return rag_service.generate_response(
        user_message=request.message,
        session_id=request.session_id
    )
