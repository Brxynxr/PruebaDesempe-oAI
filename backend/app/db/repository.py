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
    def add_message(
        db: Session, 
        conversation_id: int, 
        remitente: str, 
        contenido: str,
        sender_username: Optional[str] = None
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            remitente=remitente,
            contenido=contenido,
            sender_username=sender_username
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
        
        # If already claimed by the same agent and still in attention, return it; otherwise return None
        conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if conv and conv.estado == "en_atencion" and conv.agente_asignado == agent_username:
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
    def cleanup_old_resolved_conversations(db: Session, max_age_minutes: int = 30) -> int:
        """
        Deletes all conversations in 'resuelto' state that were resolved more than max_age_minutes ago.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        stmt = select(Conversation).where(
            Conversation.estado == "resuelto",
            Conversation.updated_at <= cutoff_time
        )
        resolved_convs = list(db.scalars(stmt).all())
        count = len(resolved_convs)
        for conv in resolved_convs:
            for msg in conv.messages:
                db.delete(msg)
            db.delete(conv)
        if count > 0:
            db.commit()
        return count

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

    @staticmethod
    def delete_conversation(db: Session, conversation_id: int) -> bool:
        """
        Deletes a conversation and its messages.
        """
        conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if not conv:
            return False
        # Delete associated messages first
        for msg in conv.messages:
            db.delete(msg)
        db.delete(conv)
        db.commit()
        return True

    @staticmethod
    def delete_conversations_bulk(db: Session, conversation_ids: List[int]) -> int:
        """
        Deletes multiple conversations and their messages in a single transaction.
        Returns the count of deleted conversations.
        """
        if not conversation_ids:
            return 0
        deleted_count = 0
        for cid in conversation_ids:
            conv = ConversationRepository.get_conversation_by_id(db, cid)
            if conv:
                for msg in conv.messages:
                    db.delete(msg)
                db.delete(conv)
                deleted_count += 1
        db.commit()
        return deleted_count

    @staticmethod
    def update_conversation(
        db: Session, 
        conversation_id: int, 
        estado: Optional[str] = None, 
        agente_asignado: Optional[str] = None,
        idioma: Optional[str] = None
    ) -> Optional[Conversation]:
        conv = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if not conv:
            return None
        if estado is not None:
            conv.estado = estado
        if agente_asignado is not None:
            conv.agente_asignado = agente_asignado
        if idioma is not None:
            conv.idioma = idioma
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def create_custom_conversation(
        db: Session,
        session_id: str,
        idioma: str = "es",
        estado: str = "pendiente",
        initial_message: Optional[str] = None
    ) -> Conversation:
        conv = Conversation(
            session_id=session_id,
            idioma=idioma,
            estado=estado,
            agente_asignado=None
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        if initial_message:
            ConversationRepository.add_message(db, conv.id, remitente="user", contenido=initial_message)
            db.refresh(conv)
        return conv

    @staticmethod
    def purge_all_conversations(db: Session) -> int:
        """
        Deletes all conversations and messages from database to clean test data.
        """
        count = db.query(Conversation).count()
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.commit()
        return count

    @staticmethod
    def get_conversation_stats(db: Session) -> Dict[str, Any]:
        """
        Calculates conversation statistics from the SQLite database:
        - Total conversations
        - Count by status (pendiente, en_atencion, resuelto, bot)
        - Count by language (es, en, fr, pt)
        - Total messages recorded
        """
        total = db.query(Conversation).count()
        pending = db.query(Conversation).filter(Conversation.estado == "pendiente").count()
        in_progress = db.query(Conversation).filter(Conversation.estado == "en_atencion").count()
        resolved = db.query(Conversation).filter(Conversation.estado == "resuelto").count()
        bot_only = db.query(Conversation).filter(Conversation.estado == "bot").count()
        
        # Languages
        lang_es = db.query(Conversation).filter(Conversation.idioma == "es").count()
        lang_en = db.query(Conversation).filter(Conversation.idioma == "en").count()
        lang_fr = db.query(Conversation).filter(Conversation.idioma == "fr").count()
        lang_pt = db.query(Conversation).filter(Conversation.idioma == "pt").count()
        
        total_messages = db.query(Message).count()
        
        return {
            "total_conversations": total,
            "pending_conversations": pending,
            "in_progress_conversations": in_progress,
            "resolved_conversations": resolved,
            "bot_conversations": bot_only,
            "languages": {
                "es": lang_es,
                "en": lang_en,
                "fr": lang_fr,
                "pt": lang_pt
            },
            "total_messages": total_messages
        }


class AdminUserRepository:
    """
    CRUD repository for managing admin and advisor user accounts.
    """

    @staticmethod
    def get_all_users(db: Session) -> List[AdminUser]:
        stmt = select(AdminUser).order_by(AdminUser.created_at.asc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[AdminUser]:
        stmt = select(AdminUser).where(AdminUser.id == user_id)
        return db.scalars(stmt).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[AdminUser]:
        stmt = select(AdminUser).where(AdminUser.username == username)
        return db.scalars(stmt).first()

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        password_hash: str,
        full_name: Optional[str] = None,
        role: str = "asesor"
    ) -> AdminUser:
        user = AdminUser(
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        password_hash: Optional[str] = None
    ) -> Optional[AdminUser]:
        user = AdminUserRepository.get_user_by_id(db, user_id)
        if not user:
            return None
        if full_name is not None:
            user.full_name = full_name
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if password_hash is not None:
            user.password_hash = password_hash
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user
