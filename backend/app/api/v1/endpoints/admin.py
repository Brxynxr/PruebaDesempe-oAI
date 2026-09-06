import os
import shutil
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.auth import (
    verify_password, 
    create_access_token, 
    get_current_admin_user, 
    decode_access_token
)
from app.core.security import verify_api_key
from app.db.session import get_db
from app.db.models import AdminUser, Conversation, Message
from app.db.repository import ConversationRepository
from app.schemas.admin import (
    AdminLoginRequest, 
    AdminLoginResponse, 
    ConversationSummary, 
    ConversationDetail, 
    MessageOut, 
    DocumentUploadResponse, 
    AgentMessageRequest,
    ConversationUpdateRequest,
    ConversationCreateRequest
)
from app.services.ingestion_service import IngestionService
from app.db.vector_store import VectorStore
from app.services.connection_manager import manager

logger = logging.getLogger("lumina.admin")
router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/login", response_model=AdminLoginResponse, summary="Admin and Agent login")
def login_admin(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    Validates admin credentials and generates a JWT Bearer token.
    """
    stmt = select(AdminUser).where(AdminUser.username == payload.username)
    user = db.scalars(stmt).first()
    
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas: usuario o contraseña no válidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username
    )

@router.get("/me", summary="Get current logged-in admin user info")
def get_current_user_profile(current_user: AdminUser = Depends(get_current_admin_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "created_at": current_user.created_at
    }

@router.post(
    "/documents/upload", 
    response_model=DocumentUploadResponse, 
    summary="Upload knowledge base Markdown document and trigger ChromaDB re-indexing"
)
async def upload_and_reindex_document(
    file: UploadFile = File(...),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Uploads a .md business file to backend/app/data/ and triggers complete re-indexing.
    """
    if not file.filename.endswith(".md"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos de texto Markdown con extensión .md"
        )

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error("Error saving uploaded document: %s", str(e))
        raise HTTPException(status_code=500, detail="Error al guardar el archivo en el servidor.")
    finally:
        await file.close()

    # Reindex ChromaDB with existing pipeline and active embedding model
    try:
        ingestion = IngestionService(data_dir=data_dir)
        docs = ingestion.load_documents()
        chunks = ingestion.create_chunks(docs)
        
        vector_store = VectorStore(collection_name="academia_lumina_kb")
        vector_store.add_chunks(chunks)
        total_indexed = vector_store.count()
        logger.info("ChromaDB re-indexed successfully. Total chunks: %d", total_indexed)
    except Exception as e:
        logger.error("Error during document re-indexing: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error durante la reindexación de ChromaDB: {str(e)}")

    return DocumentUploadResponse(
        status="success",
        filename=file.filename,
        total_chunks=total_indexed,
        message=f"Documento '{file.filename}' subido y base de datos vectorial reindexada exitosamente ({len(chunks)} fragmentos procesados)."
    )

@router.get("/conversations/pending", response_model=List[ConversationSummary], summary="List all pending escalated conversations")
def list_pending_conversations(
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Lists conversations in 'pendiente' status for human agent inbox.
    """
    convs = ConversationRepository.get_pending_conversations(db)
    results = []
    for c in convs:
        last_msg = c.messages[-1].contenido if c.messages else None
        results.append(ConversationSummary(
            id=c.id,
            session_id=c.session_id,
            idioma=c.idioma,
            estado=c.estado,
            agente_asignado=c.agente_asignado,
            created_at=c.created_at,
            updated_at=c.updated_at,
            last_message=last_msg,
            message_count=len(c.messages)
        ))
    return results

@router.get("/conversations", response_model=List[ConversationSummary], summary="List all conversations with optional status filter")
def list_all_conversations(
    estado: Optional[str] = None,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Lists all conversations in the database.
    Automatically prunes resolved conversations older than 30 minutes.
    """
    ConversationRepository.cleanup_old_resolved_conversations(db, max_age_minutes=30)
    
    stmt = select(Conversation)
    if estado and estado != "all":
        stmt = stmt.where(Conversation.estado == estado)
    elif not estado:
        # Por defecto solo mostrar conversaciones escaladas a asesores
        stmt = stmt.where(Conversation.estado.in_(["pendiente", "en_atencion", "resuelto"]))
    stmt = stmt.order_by(Conversation.updated_at.desc())
    convs = list(db.scalars(stmt).all())
    
    results = []
    for c in convs:
        last_msg = c.messages[-1].contenido if c.messages else None
        results.append(ConversationSummary(
            id=c.id,
            session_id=c.session_id,
            idioma=c.idioma,
            estado=c.estado,
            agente_asignado=c.agente_asignado,
            created_at=c.created_at,
            updated_at=c.updated_at,
            last_message=last_msg,
            message_count=len(c.messages)
        ))
    return results

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail, summary="Get full conversation details and history")
def get_conversation_detail(
    conversation_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Returns complete conversation message history.
    """
    conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    
    messages_out = [
        MessageOut(
            id=m.id,
            remitente=m.remitente,
            contenido=m.contenido,
            timestamp=m.timestamp
        ) for m in conv.messages
    ]
    
    return ConversationDetail(
        id=conv.id,
        session_id=conv.session_id,
        idioma=conv.idioma,
        estado=conv.estado,
        agente_asignado=conv.agente_asignado,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages_out
    )

@router.post("/conversations/{conversation_id}/claim", response_model=ConversationDetail, summary="Claim a conversation by an agent")
async def claim_conversation(
    conversation_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Transitions conversation to 'en_atencion' and assigns to current agent.
    """
    conv = ConversationRepository.claim_conversation(db, conversation_id, current_user.username)
    if not conv:
        existing = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if existing and existing.estado == "en_atencion":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Esta conversación ya fue tomada por el asesor '{existing.agente_asignado}'."
            )
        raise HTTPException(status_code=404, detail="Conversación no disponible o no encontrada.")
    
    # Notify user via WebSocket that an agent has joined
    await manager.send_to_user(conv.session_id, {
        "type": "agent_connected",
        "agent_name": current_user.username,
        "message": f"El asesor {current_user.username} se ha unido al chat." if conv.idioma == "es" else f"Advisor {current_user.username} has joined the chat."
    })
    
    # Broadcast status update to other agents
    await manager.broadcast_to_agents({
        "type": "conversation_claimed",
        "conversation_id": conv.id,
        "session_id": conv.session_id,
        "agent_username": current_user.username
    })

    messages_out = [
        MessageOut(
            id=m.id,
            remitente=m.remitente,
            contenido=m.contenido,
            timestamp=m.timestamp
        ) for m in conv.messages
    ]

    return ConversationDetail(
        id=conv.id,
        session_id=conv.session_id,
        idioma=conv.idioma,
        estado=conv.estado,
        agente_asignado=conv.agente_asignado,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages_out
    )

@router.post("/conversations/{conversation_id}/resolve", response_model=ConversationDetail, summary="Mark conversation as resolved")
async def resolve_conversation(
    conversation_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Transitions conversation to 'resuelto'.
    """
    conv = ConversationRepository.resolve_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    # Notify user via WebSocket that the conversation was resolved
    await manager.send_to_user(conv.session_id, {
        "type": "conversation_resolved",
        "message": "La conversación ha sido resuelta por el asesor. ¡Gracias por comunicarte con Academia Lumina!" if conv.idioma == "es" else "The conversation has been marked as resolved by the advisor. Thank you for contacting Academia Lumina!"
    })

    # Broadcast update to agents
    await manager.broadcast_to_agents({
        "type": "conversation_resolved",
        "conversation_id": conv.id,
        "session_id": conv.session_id
    })

    messages_out = [
        MessageOut(
            id=m.id,
            remitente=m.remitente,
            contenido=m.contenido,
            timestamp=m.timestamp
        ) for m in conv.messages
    ]

    return ConversationDetail(
        id=conv.id,
        session_id=conv.session_id,
        idioma=conv.idioma,
        estado=conv.estado,
        agente_asignado=conv.agente_asignado,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages_out
    )

@router.post("/conversations/{conversation_id}/messages", summary="Send an agent response message in real time to the student")
async def send_agent_message(
    conversation_id: int,
    payload: AgentMessageRequest,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Appends an agent message to the conversation and dispatches it immediately via WebSocket to the student.
    Strictly validates that the conversation has been claimed by an advisor before allowing responses.
    """
    conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    # Validation 1: Case must be claimed before sending messages
    if conv.estado == "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes tomar el caso ('Tomar Caso') antes de poder responder al estudiante."
        )

    # Validation 2: Cannot send messages to resolved conversations
    if conv.estado == "resuelto":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta conversación ya está marcada como resuelta. No se pueden enviar nuevos mensajes."
        )

    # Validation 3: Cannot send messages if assigned to another advisor (superadmin 'admin' can override)
    if conv.agente_asignado and conv.agente_asignado != current_user.username and current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Este caso está asignado al asesor '{conv.agente_asignado}'. No puedes responder en su nombre."
        )

    # Store agent message in DB
    msg = ConversationRepository.add_message(db, conv.id, remitente="agent", contenido=payload.message)

    # Dispatch to student WebSocket
    await manager.send_to_user(conv.session_id, {
        "type": "agent_message",
        "sender": "agent",
        "agent_name": current_user.username,
        "message": payload.message,
        "timestamp": msg.timestamp.isoformat()
    })

    return {
        "status": "sent",
        "message_id": msg.id,
        "timestamp": msg.timestamp
    }

@router.post("/conversations", response_model=ConversationDetail, summary="Create a manual or simulated conversation")
def create_conversation(
    payload: ConversationCreateRequest,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new conversation ticket from the admin backoffice.
    """
    conv = ConversationRepository.create_custom_conversation(
        db,
        session_id=payload.session_id,
        idioma=payload.idioma or "es",
        estado=payload.estado or "pendiente",
        initial_message=payload.initial_message
    )
    messages_out = [
        MessageOut(
            id=m.id,
            remitente=m.remitente,
            contenido=m.contenido,
            timestamp=m.timestamp
        ) for m in conv.messages
    ]
    return ConversationDetail(
        id=conv.id,
        session_id=conv.session_id,
        idioma=conv.idioma,
        estado=conv.estado,
        agente_asignado=conv.agente_asignado,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages_out
    )

@router.put("/conversations/{conversation_id}", response_model=ConversationDetail, summary="Update conversation status, language or assigned advisor")
async def update_conversation_status(
    conversation_id: int,
    payload: ConversationUpdateRequest,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Updates conversation fields (estado, agente_asignado, idioma).
    """
    conv = ConversationRepository.update_conversation(
        db,
        conversation_id=conversation_id,
        estado=payload.estado,
        agente_asignado=payload.agente_asignado,
        idioma=payload.idioma
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    # Broadcast update to agents
    await manager.broadcast_to_agents({
        "type": "conversation_updated",
        "conversation_id": conv.id,
        "estado": conv.estado,
        "agente_asignado": conv.agente_asignado
    })

    messages_out = [
        MessageOut(
            id=m.id,
            remitente=m.remitente,
            contenido=m.contenido,
            timestamp=m.timestamp
        ) for m in conv.messages
    ]
    return ConversationDetail(
        id=conv.id,
        session_id=conv.session_id,
        idioma=conv.idioma,
        estado=conv.estado,
        agente_asignado=conv.agente_asignado,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages_out
    )

@router.delete("/conversations/clear-all", summary="Purge and clean all conversations and test records from database")
async def clear_all_conversations(
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Cleans all conversations and messages from database.
    """
    deleted_count = ConversationRepository.purge_all_conversations(db)

    # Broadcast reset to all connected agents
    await manager.broadcast_to_agents({
        "type": "conversation_deleted",
        "conversation_id": "all"
    })

    return {
        "status": "cleared",
        "deleted_count": deleted_count,
        "message": f"Se eliminaron {deleted_count} conversaciones y se limpió la base de datos."
    }

@router.delete("/conversations/{conversation_id}", summary="Delete a conversation and its messages")
async def delete_conversation(
    conversation_id: int,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes a conversation and all its messages.
    """
    success = ConversationRepository.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")

    # Broadcast deletion to agents
    await manager.broadcast_to_agents({
        "type": "conversation_deleted",
        "conversation_id": conversation_id
    })

    return {"status": "deleted", "conversation_id": conversation_id, "message": "Conversación eliminada correctamente."}

@router.get("/conversations/sla/breached", summary="Get pending conversations breaching SLA threshold (for n8n & monitoring)")
def get_sla_breached_conversations(
    request: Request,
    threshold_minutes: int = Query(10, ge=1, le=1440),
    db: Session = Depends(get_db)
):
    """
    Accepts either X-API-Key (for n8n automated jobs) or Admin JWT Bearer token.
    Returns list of conversations in 'pendiente' status for longer than threshold_minutes.
    """
    # 1. Check if valid X-API-Key is present
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key == settings.BACKEND_API_KEY:
        auth_ok = True
    else:
        # 2. Check for Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                decode_access_token(token)
                auth_ok = True
            except Exception:
                auth_ok = False
        else:
            auth_ok = False

    if not auth_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida vía 'X-API-Key' o 'Authorization: Bearer <token>'."
        )

    breached = ConversationRepository.get_sla_breached_conversations(db, threshold_minutes=threshold_minutes)
    return [
        {
            "id": c.id,
            "session_id": c.session_id,
            "idioma": c.idioma,
            "estado": c.estado,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
            "pending_minutes": round((datetime.now(c.updated_at.tzinfo or timezone.utc) - c.updated_at).total_seconds() / 60, 1),
            "last_message": c.messages[-1].contenido if c.messages else ""
        }
        for c in breached
    ]
