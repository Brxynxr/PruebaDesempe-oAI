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
    role: str = "asesor"
    full_name: Optional[str] = None

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remitente: str
    contenido: str
    sender_username: Optional[str] = None
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

class ConversationUpdateRequest(BaseModel):
    estado: Optional[str] = Field(None, description="New status: pendiente, en_atencion, resuelto, bot")
    agente_asignado: Optional[str] = Field(None, description="Assigned advisor username")
    idioma: Optional[str] = Field(None, description="Language: es, en, fr, pt")

class ConversationCreateRequest(BaseModel):
    session_id: str = Field(..., description="Unique session ID")
    idioma: Optional[str] = Field("es", description="Language code")
    estado: Optional[str] = Field("pendiente", description="Initial status")
    initial_message: Optional[str] = Field(None, description="Initial student message")

class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full Name")
    role: str = Field("asesor", description="Role: 'admin' or 'asesor'")

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, description="Updated Full Name")
    role: Optional[str] = Field(None, description="Updated Role")
    is_active: Optional[bool] = Field(None, description="Active status")
    password: Optional[str] = Field(None, min_length=6, description="New password")

class BulkDeleteConversationsRequest(BaseModel):
    conversation_ids: List[int] = Field(..., min_length=1, description="List of conversation IDs to delete")

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
