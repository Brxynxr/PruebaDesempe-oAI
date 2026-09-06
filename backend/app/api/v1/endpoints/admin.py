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
    hash_password,
    create_access_token, 
    get_current_admin_user, 
    require_admin_role,
    decode_access_token
)
from app.core.security import verify_api_key
from app.db.session import get_db
from app.db.models import AdminUser, Conversation, Message
from app.db.repository import ConversationRepository, AdminUserRepository
from app.schemas.admin import (
    AdminLoginRequest, 
    AdminLoginResponse, 
    ConversationSummary, 
    ConversationDetail, 
    MessageOut, 
    DocumentUploadResponse, 
    AgentMessageRequest,
    ConversationUpdateRequest,
    ConversationCreateRequest,
    UserCreateRequest,
    UserUpdateRequest,
    UserOut,
    BulkDeleteConversationsRequest
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
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta de usuario ha sido desactivada por el administrador.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        role=user.role,
        full_name=user.full_name
    )

@router.get("/me", summary="Get current logged-in admin user info")
def get_current_user_profile(current_user: AdminUser = Depends(get_current_admin_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

# ==============================================================================
# USER & ADVISOR MANAGEMENT (SUPERADMIN ONLY)
# ==============================================================================

@router.get("/users", response_model=List[UserOut], summary="List all advisors and admin users")
def list_users(
    current_admin: AdminUser = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    Lists all advisor and admin accounts in the database. Only accessible to users with role 'admin'.
    """
    return AdminUserRepository.get_all_users(db)

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create a new advisor account")
def create_user(
    payload: UserCreateRequest,
    current_admin: AdminUser = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    Creates a new advisor or admin user account with bcrypt password hashing.
    """
    existing = AdminUserRepository.get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El nombre de usuario '{payload.username}' ya está registrado."
        )
    
    hashed = hash_password(payload.password)
    new_user = AdminUserRepository.create_user(
        db=db,
        username=payload.username,
        password_hash=hashed,
        full_name=payload.full_name,
        role=payload.role if payload.role in ("admin", "asesor") else "asesor"
    )
    logger.info("Admin %s created user %s with role %s", current_admin.username, new_user.username, new_user.role)
    return new_user

@router.patch("/users/{user_id}", response_model=UserOut, summary="Update advisor account status or role")
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    current_admin: AdminUser = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    Updates role, active status, full name, or resets password for an advisor account.
    """
    user = AdminUserRepository.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    
    # Prevent self-deactivation of the primary superadmin
    if user.id == current_admin.id and payload.is_active is False:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta de administrador.")

    password_hash = hash_password(payload.password) if payload.password else None
    updated_user = AdminUserRepository.update_user(
        db=db,
        user_id=user_id,
        full_name=payload.full_name,
        role=payload.role,
        is_active=payload.is_active,
        password_hash=password_hash
    )
    return updated_user

@router.get(
    "/documents",
    summary="List all indexed knowledge base documents (PDF, DOCX, TXT, MD)"
)
def list_documents(
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Returns list of all uploaded knowledge documents in backend/app/data/.
    """
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")
    if not os.path.exists(data_dir):
        return []
    
    docs = []
    allowed_exts = [".pdf", ".docx", ".doc", ".txt", ".md"]
    for fname in sorted(os.listdir(data_dir)):
        fpath = os.path.join(data_dir, fname)
        if os.path.isfile(fpath):
            ext = os.path.splitext(fname)[1].lower()
            if ext in allowed_exts:
                stat = os.stat(fpath)
                docs.append({
                    "filename": fname,
                    "extension": ext.replace(".", "").upper(),
                    "size_bytes": stat.st_size,
                    "size_formatted": f"{(stat.st_size / 1024):.1f} KB" if stat.st_size < 1024 * 1024 else f"{(stat.st_size / (1024*1024)):.2f} MB",
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                })
    return docs

@router.post(
    "/documents/upload", 
    response_model=DocumentUploadResponse, 
    summary="Upload knowledge base document (PDF, Word DOCX, TXT, MD) and trigger ChromaDB re-indexing"
)
async def upload_and_reindex_document(
    file: UploadFile = File(...),
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Uploads a business file (.pdf, .docx, .txt, .md) to backend/app/data/ and triggers vector re-indexing.
    """
    allowed_exts = [".pdf", ".docx", ".doc", ".txt", ".md"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no compatible. Solo se permiten archivos {', '.join(allowed_exts)}"
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

    # Reindex ChromaDB with IngestionService supporting PDF, DOCX, TXT, MD
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
        message=f"Documento '{file.filename}' ({file_ext.upper()}) procesado e indexado exitosamente en ChromaDB."
    )

@router.delete(
    "/documents/{filename}",
    summary="Delete a knowledge base document and remove its embeddings from ChromaDB"
)
def delete_document(
    filename: str,
    current_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Deletes the document file from disk and removes its associated vector chunks from ChromaDB.
    """
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")
    file_path = os.path.join(data_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Documento '{filename}' no encontrado.")

    try:
        os.remove(file_path)
    except Exception as e:
        logger.error("Error deleting file '%s': %s", filename, str(e))
        raise HTTPException(status_code=500, detail="Error al eliminar el archivo del servidor.")

    # Remove associated chunks from ChromaDB
    try:
        vector_store = VectorStore(collection_name="academia_lumina_kb")
        vector_store.delete_by_source(filename)
        total_remaining = vector_store.count()
        logger.info("Deleted document '%s'. Remaining chunks: %d", filename, total_remaining)
    except Exception as e:
        logger.warning("Error deleting vector embeddings for '%s': %s", filename, str(e))
        total_remaining = 0

    return {
        "status": "deleted",
        "filename": filename,
        "remaining_chunks": total_remaining,
        "message": f"Documento '{filename}' eliminado exitosamente de la base de conocimiento."
    }

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
            sender_username=m.sender_username,
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
        if existing and existing.estado == "resuelto":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta conversación ya ha sido resuelta y finalizada."
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
            sender_username=m.sender_username,
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

@router.post("/conversations/{conversation_id}/resolve", response_model=ConversationDetail, summary="Resolve a conversation")
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

    # Notify Telegram channel so advisors are aware the case is closed
    try:
        from app.services.telegram_service import TelegramService
        TelegramService.send_message_async(
            f"<b>CASO RESUELTO EN PANEL WEB</b> (Sesión: <code>{conv.session_id}</code>)\n"
            "────────────────────────────\n"
            f"El asesor <b>{current_user.username}</b> ha marcado este caso como resuelto desde el panel de control."
        )
    except Exception as e:
        logger.debug("Error notificando resolución a Telegram: %s", str(e))

    messages_out = [
        MessageOut(
            id=m.id,
            remitente=m.remitente,
            contenido=m.contenido,
            sender_username=m.sender_username,
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

    # Validation 3: Cannot send messages if assigned to another advisor (only users with role 'admin' can override)
    if conv.agente_asignado and conv.agente_asignado != current_user.username and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Este caso está asignado al asesor '{conv.agente_asignado}'. No puedes responder en su nombre sin permisos de Administrador."
        )

    # Store agent message in DB with sender audit
    msg = ConversationRepository.add_message(
        db, 
        conv.id, 
        remitente="agent", 
        contenido=payload.message,
        sender_username=current_user.username
    )

    # Dispatch to student WebSocket
    await manager.send_to_user(conv.session_id, {
        "type": "agent_message",
        "sender": "agent",
        "agent_name": current_user.full_name or current_user.username,
        "message": payload.message,
        "timestamp": msg.timestamp.isoformat()
    })

    return {
        "status": "sent",
        "message_id": msg.id,
        "sender_username": current_user.username,
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
            sender_username=m.sender_username,
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
            sender_username=m.sender_username,
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

@router.post("/conversations/bulk-delete", summary="Bulk delete multiple conversations and their messages")
async def bulk_delete_conversations(
    payload: BulkDeleteConversationsRequest,
    current_user: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes multiple conversations and their message history in a single request.
    """
    deleted_count = ConversationRepository.delete_conversations_bulk(db, payload.conversation_ids)
    
    # Broadcast bulk deletion to all connected agent dashboards
    await manager.broadcast_to_agents({
        "type": "conversations_bulk_deleted",
        "conversation_ids": payload.conversation_ids,
        "count": deleted_count
    })

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "message": f"Se eliminaron {deleted_count} conversaciones correctamente."
    }

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
    res = []
    now_utc = datetime.now(timezone.utc)
    for c in breached:
        up_at = c.updated_at if (c.updated_at and c.updated_at.tzinfo) else (c.updated_at.replace(tzinfo=timezone.utc) if c.updated_at else now_utc)
        pending_minutes = round((now_utc - up_at).total_seconds() / 60, 1)
        res.append({
            "id": c.id,
            "session_id": c.session_id,
            "idioma": c.idioma,
            "estado": c.estado,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "pending_minutes": max(0.0, pending_minutes),
            "last_message": c.messages[-1].contenido if c.messages else ""
        })
    return res
