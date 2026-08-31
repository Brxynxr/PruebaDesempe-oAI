from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """
    Esquema de solicitud de consulta por parte del usuario o del flujo de n8n.
    """
    message: str = Field(..., min_length=1, description="Mensaje o pregunta del usuario")
    session_id: Optional[str] = Field(default="default", description="Identificador único de sesión para contexto")

class SourceDocument(BaseModel):
    """
    Esquema para representar los documentos o fragmentos utilizados en la respuesta del RAG.
    """
    content: str = Field(..., description="Contenido del fragmento recuperado")
    source: str = Field(..., description="Nombre del documento de origen")
    score: Optional[float] = Field(default=None, description="Puntaje de similitud semántica")

class ChatResponse(BaseModel):
    """
    Esquema de respuesta devuelto por el servicio RAG.
    """
    response: str = Field(..., description="Respuesta generada por el LLM")
    is_escalated: bool = Field(default=False, description="Indica si la consulta requiere escalamiento a humano")
    whatsapp_link: Optional[str] = Field(default=None, description="Enlace directo a WhatsApp en caso de escalamiento")
    sources: List[SourceDocument] = Field(default_factory=list, description="Fuentes consultadas en la base vectorial")
    session_id: str = Field(..., description="ID de sesión asociado")

class HealthResponse(BaseModel):
    """
    Esquema para el estado de salud del servicio.
    """
    status: str = Field(..., description="Estado general de la aplicación (ok/degraded)")
    version: str = Field(..., description="Versión actual de la API")
    environment: str = Field(..., description="Entorno de ejecución")
