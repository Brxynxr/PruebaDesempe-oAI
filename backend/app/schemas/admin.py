from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=2, description="Admin username")
    password: str = Field(..., min_length=4, description="Admin password")

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remitente: str
    contenido: str
    timestamp: datetime

class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    idioma: str
    estado: str
    agente_asignado: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
    message_count: int = 0

class ConversationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    idioma: str
    estado: str
    agente_asignado: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageOut] = []

class DocumentUploadResponse(BaseModel):
    status: str
    filename: str
    total_chunks: int
    message: str

class AgentMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message content from the agent")
