from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """
    Schema for user chat inquiry requests.
    """
    message: str = Field(..., min_length=1, description="User message or question")
    session_id: Optional[str] = Field(default="default", description="Unique session identifier for tracking")
    language: Optional[str] = Field(default="en", description="Language of response ('en' or 'es')")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Recent conversation history turns")

    @field_validator('message')
    @classmethod
    def validate_message_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty or contain only whitespace.")
        return cleaned

class LeadRequest(BaseModel):
    """
    Schema for registering student lead contact data.
    """
    name: str = Field(..., min_length=2, description="Student name")
    phone: str = Field(..., min_length=7, description="Student WhatsApp/phone number")
    program: Optional[str] = Field(default="Inglés", description="Program of interest (English, French, Portuguese)")
    user_message: Optional[str] = Field(default="", description="Original query from the student")
    session_id: Optional[str] = Field(default="default", description="Session ID")
    language: Optional[str] = Field(default="en", description="Language code")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return cleaned

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 7:
            raise ValueError("Phone number must have at least 7 digits.")
        return cleaned

class SourceDocument(BaseModel):
    """
    Schema representing document chunks retrieved from the vector database.
    """
    content: str = Field(..., description="Retrieved chunk content")
    source: str = Field(..., description="Source file name")
    score: Optional[float] = Field(default=None, description="Semantic similarity score")

class ChatResponse(BaseModel):
    """
    Response schema returned by the RAG service.
    """
    response: str = Field(..., description="Response synthesized by the LLM")
    is_escalated: bool = Field(default=False, description="Indicates if the query requires human escalation")
    is_closed: bool = Field(default=False, description="Indicates if the conversation reached a closing or farewell state")
    whatsapp_link: Optional[str] = Field(default=None, description="Direct WhatsApp link in case of escalation")
    sources: List[SourceDocument] = Field(default_factory=list, description="Sources consulted in the vector database")
    session_id: str = Field(..., description="Associated session ID")

class HealthResponse(BaseModel):
    """
    Schema for service health status.
    """
    status: str = Field(..., description="General service status (ok/degraded)")
    version: str = Field(..., description="Current application version")
    environment: str = Field(..., description="Active execution environment")
