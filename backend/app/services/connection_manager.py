import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger("lumina.websocket")

class ConnectionManager:
    """
    Manages real-time WebSocket connections for both students (by session_id)
    and human support agents (broadcast channel).
    """

    def __init__(self):
        # Maps session_id -> list of active WebSocket connections for that student
        self.active_user_connections: Dict[str, List[WebSocket]] = {}
        # Set of active agent WebSocket connections
        self.active_agent_connections: Set[WebSocket] = set()

    async def connect_user(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_user_connections:
            self.active_user_connections[session_id] = []
        self.active_user_connections[session_id].append(websocket)
        logger.info("[WebSocket] User connected on session: %s", session_id)

    def disconnect_user(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_user_connections:
            if websocket in self.active_user_connections[session_id]:
                self.active_user_connections[session_id].remove(websocket)
            if not self.active_user_connections[session_id]:
                del self.active_user_connections[session_id]
        logger.info("[WebSocket] User disconnected from session: %s", session_id)

    async def connect_agent(self, websocket: WebSocket):
        await websocket.accept()
        self.active_agent_connections.add(websocket)
        logger.info("[WebSocket] Agent connected to live channel")

    def disconnect_agent(self, websocket: WebSocket):
        self.active_agent_connections.discard(websocket)
        logger.info("[WebSocket] Agent disconnected from live channel")

    async def send_to_user(self, session_id: str, message: dict):
        """Sends a JSON message to all open WebSockets for a specific user session."""
        if session_id in self.active_user_connections:
            for connection in list(self.active_user_connections[session_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning("[WebSocket] Failed sending to user %s: %s", session_id, str(e))
                    self.disconnect_user(connection, session_id)

    async def broadcast_to_agents(self, message: dict):
        """Broadcasts an event or message to all connected agent screens."""
        for connection in list(self.active_agent_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("[WebSocket] Failed sending to agent: %s", str(e))
                self.disconnect_agent(connection)

manager = ConnectionManager()
