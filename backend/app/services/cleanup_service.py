import asyncio
import logging
from typing import Optional
from app.db.session import SessionLocal
from app.db.repository import ConversationRepository

logger = logging.getLogger("lumina.cleanup")

class CleanupService:
    """
    Background worker service that periodically purges resolved conversations
    that are older than the specified retention period (default 30 minutes).
    """
    _task: Optional[asyncio.Task] = None
    _running: bool = False

    @classmethod
    def start_periodic_cleanup(cls, interval_seconds: int = 60, max_age_minutes: int = 30):
        """
        Starts the asynchronous periodic cleanup loop in the background.
        """
        if cls._running:
            return
        cls._running = True
        cls._task = asyncio.create_task(cls._cleanup_loop(interval_seconds, max_age_minutes))
        logger.info(
            "Automatic resolved conversation cleanup worker started (interval=%ds, max_age=%dm).",
            interval_seconds,
            max_age_minutes
        )

    @classmethod
    async def _cleanup_loop(cls, interval_seconds: int, max_age_minutes: int):
        while cls._running:
            try:
                await asyncio.sleep(interval_seconds)
                with SessionLocal() as db:
                    deleted_count = ConversationRepository.cleanup_old_resolved_conversations(
                        db, 
                        max_age_minutes=max_age_minutes
                    )
                    if deleted_count > 0:
                        logger.info(
                            "Auto-cleanup pruned %d resolved conversation(s) older than %d minutes.",
                            deleted_count,
                            max_age_minutes
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in automatic conversation cleanup worker: %s", str(e))

    @classmethod
    def stop_periodic_cleanup(cls):
        """
        Stops the periodic cleanup loop gracefully.
        """
        cls._running = False
        if cls._task and not cls._task.done():
            cls._task.cancel()
        logger.info("Automatic resolved conversation cleanup worker stopped.")
