from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, desc
from app.db.models import Conversation, Message, AdminUser

class ConversationRepository:
    """
    CRUD repository for conversations and messages with atomic transactions.
    """

    @staticmethod
    def get_or_create_conversation(db: Session, session_id: str, idioma: str = "es") -> Conversation:
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        conv = db.scalars(stmt).first()
        if not conv:
            conv = Conversation(
                session_id=session_id,
                idioma=idioma,
                estado="bot",
                agente_asignado=None
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)
        return conv

    @staticmethod
    def add_message(db: Session, conversation_id: int, remitente: str, contenido: str) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            remitente=remitente,
            contenido=contenido
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def record_interaction(
        db: Session, 
        session_id: str, 
        user_message: str, 
        bot_response: str, 
        is_escalated: bool = False,
        idioma: str = "es"
    ) -> Conversation:
        """
        Records a user query and bot response turn into SQLite.
        If escalated, marks conversation state as 'pendiente'.
        """
        conv = ConversationRepository.get_or_create_conversation(db, session_id, idioma=idioma)
        
        # Add user message
        ConversationRepository.add_message(db, conv.id, remitente="user", contenido=user_message)
        
        # Add bot message
        ConversationRepository.add_message(db, conv.id, remitente="bot", contenido=bot_response)

        # Update status if escalated and not already claimed by an agent
        if is_escalated and conv.estado in ("bot", "resuelto"):
            conv.estado = "pendiente"
            conv.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(conv)

        return conv

    @staticmethod
    def get_pending_conversations(db: Session) -> List[Conversation]:
        """
        Returns all conversations currently in 'pendiente' state, ordered by most recently updated.
        """
        stmt = select(Conversation).where(Conversation.estado == "pendiente").order_by(desc(Conversation.updated_at))
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_conversation_by_id(db: Session, conversation_id: int) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        return db.scalars(stmt).first()

    @staticmethod
    def get_conversation_by_session_id(db: Session, session_id: str) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        return db.scalars(stmt).first()

    @staticmethod
    def claim_conversation(db: Session, conversation_id: int, agent_username: str) -> Optional[Conversation]:
        """
        Atomically claims a conversation for an agent, preventing race conditions.
        Only transitions if the conversation is currently in 'pendiente' state.
        """
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id, Conversation.estado == "pendiente")
            .values(
                estado="en_atencion",
                agente_asignado=agent_username,
                updated_at=datetime.now(timezone.utc)
            )
        )
        res = db.execute(stmt)
        db.commit()
        if res.rowcount > 0:
            return ConversationRepository.get_conversation_by_id(db, conversation_id)
        
        # If already claimed by the same agent, return it; otherwise return None
        conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if conv and conv.agente_asignado == agent_username:
            return conv
        return None

    @staticmethod
    def resolve_conversation(db: Session, conversation_id: int) -> Optional[Conversation]:
        conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if conv:
            conv.estado = "resuelto"
            conv.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(conv)
        return conv

    @staticmethod
    def get_sla_breached_conversations(db: Session, threshold_minutes: int = 10) -> List[Conversation]:
        """
        Returns conversations in 'pendiente' state with more than threshold_minutes without being claimed.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)
        stmt = select(Conversation).where(
            Conversation.estado == "pendiente",
            Conversation.updated_at <= cutoff_time
        ).order_by(Conversation.updated_at)
        return list(db.scalars(stmt).all())
