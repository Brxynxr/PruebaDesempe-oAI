import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.connection_manager import manager
from app.db.session import SessionLocal
from app.db.repository import ConversationRepository
from app.core.auth import decode_access_token

logger = logging.getLogger("lumina.ws")
router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/chat/{session_id}")
@router.websocket("/chat/{session_id}")
async def websocket_user_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for students/users.
    Keeps a persistent real-time channel open for live agent handoff and bidirectional messaging.
    """
    await manager.connect_user(websocket, session_id)
    db = SessionLocal()
    try:
        # Fetch current conversation state and history
        conv = ConversationRepository.get_conversation_by_session_id(db, session_id)
        if conv:
            messages_history = [
                {
                    "sender": m.remitente,
                    "text": m.contenido,
                    "agentName": m.sender_username if m.remitente == "agent" else None,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None
                }
                for m in conv.messages
                if m.remitente in ("user", "agent", "bot") and not (m.contenido or "").startswith("[Lead Registrado]") and not (m.contenido or "").startswith("Lead de contacto registrado:")
            ]
            await websocket.send_json({
                "type": "session_status",
                "estado": conv.estado,
                "agente_asignado": conv.agente_asignado,
                "messages": messages_history
            })

        while True:
            data_text = await websocket.receive_text()
            try:
                data = json.loads(data_text)
            except Exception:
                data = {"type": "user_message", "message": data_text}

            # If user sends a message while in 'en_atencion' or 'pendiente'
            msg_content = data.get("message", "").strip()
            if msg_content:
                conv = ConversationRepository.get_or_create_conversation(db, session_id)
                msg = ConversationRepository.add_message(db, conv.id, remitente="user", contenido=msg_content)
                
                # Notify connected agents in real time via WebSockets and Telegram
                await manager.broadcast_to_agents({
                    "type": "user_message",
                    "conversation_id": conv.id,
                    "session_id": session_id,
                    "message": msg_content,
                    "estado": conv.estado,
                    "timestamp": msg.timestamp.isoformat()
                })
                
                # Push alert to advisor on Telegram only if case is actively taken by Telegram advisor
                if conv.estado == "en_atencion" and conv.agente_asignado and "Telegram" in conv.agente_asignado:
                    from app.services.telegram_service import TelegramService
                    TelegramService.send_student_live_message(session_id=session_id, message=msg_content, conversation_id=conv.id)

    except WebSocketDisconnect:
        manager.disconnect_user(websocket, session_id)
    except Exception as e:
        logger.error("[WebSocket Error] user session %s: %s", session_id, str(e))
        manager.disconnect_user(websocket, session_id)
    finally:
        db.close()

@router.websocket("/ws/agent")
@router.websocket("/agent")
async def websocket_agent_channel(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket endpoint for agent dashboard to receive real-time updates and incoming student messages.
    """
    if not token:
        await websocket.close(code=4001, reason="Missing auth token")
        return

    try:
        payload = decode_access_token(token)
        agent_username = payload.get("sub")
        if not agent_username:
            await websocket.close(code=4001, reason="Invalid token payload")
            return
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await manager.connect_agent(websocket)
    try:
        await websocket.send_json({
            "type": "connection_established",
            "message": f"Conectado como agente: {agent_username}"
        })
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_agent(websocket)
    except Exception as e:
        logger.error("[WebSocket Agent Error]: %s", str(e))
        manager.disconnect_agent(websocket)
