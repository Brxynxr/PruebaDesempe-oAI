from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """
    Schema representing incoming user or n8n chat request payload.
    """
    message: str = Field(..., min_length=1, description="User question or query text")
    session_id: Optional[str] = Field(default="default", description="Unique session identifier for tracking")

class SourceDocument(BaseModel):
    """
    Schema representing retrieved vector context source fragment.
    """
    content: str = Field(..., description="Content text of retrieved chunk")
    source: str = Field(..., description="Source document file name")
    score: Optional[float] = Field(default=None, description="Similarity score")

class ChatResponse(BaseModel):
    """
    Schema representing output response payload from RAG service.
    """
    response: str = Field(..., description="Synthesized response from LLM")
    is_escalated: bool = Field(default=False, description="Flag indicating if human escalation is required")
    whatsapp_link: Optional[str] = Field(default=None, description="Direct WhatsApp link on escalation")
    sources: List[SourceDocument] = Field(default_factory=list, description="Retrieved vector database sources")
    session_id: str = Field(..., description="Associated session identifier")

class HealthResponse(BaseModel):
    """
    Schema representing system health check response.
    """
    status: str = Field(..., description="Overall service status (ok/degraded)")
    version: str = Field(..., description="Current application version")
    environment: str = Field(..., description="Active execution environment")
