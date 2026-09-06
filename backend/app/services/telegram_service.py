import logging
import threading
import time
import re
import urllib.request
import urllib.parse
import json
import asyncio
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger("lumina.telegram")

class TelegramService:
    """
    Omnichannel Bidirectional Telegram Service.
    - Sends rich notifications with action buttons (WhatsApp, Claim Case, Resolve).
    - Long-polls Telegram in background to receive advisor replies and push them live
      to the student's browser via WebSockets.
    - Synchronizes state with SQLite and the Admin Dashboard in real time.
    """

    _polling_thread: Optional[threading.Thread] = None
    _stop_event = threading.Event()
    _last_update_id: int = 0
    # Map telegram message_id -> session_id for direct reply routing
    _message_session_map: Dict[int, str] = {}
    _active_session_id: Optional[str] = None

    @staticmethod
    def _api_call(method: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            return None

        url = f"https://api.telegram.org/bot{token}/{method}"
        try:
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=25) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            logger.debug("[Telegram API] %s error: %s", method, str(e))
            return None

    @staticmethod
    def send_message_sync(
        text: str, 
        inline_keyboard: Optional[list] = None,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
        session_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Synchronously sends a message to Telegram and returns the telegram message_id.
        """
        target_chat = chat_id or settings.TELEGRAM_CHAT_ID
        if not settings.TELEGRAM_BOT_TOKEN or not target_chat:
            return None

        payload: Dict[str, Any] = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode
        }
        if inline_keyboard:
            payload["reply_markup"] = json.dumps({"inline_keyboard": inline_keyboard})

        res = TelegramService._api_call("sendMessage", payload)
        if res and res.get("ok"):
            msg_id = res["result"]["message_id"]
            if session_id:
                TelegramService._message_session_map[msg_id] = session_id
                TelegramService._active_session_id = session_id
            return msg_id
        return None

    @staticmethod
    def send_message_async(
        text: str, 
        inline_keyboard: Optional[list] = None,
        chat_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> None:
        """Asynchronously dispatches a message in a background daemon thread."""
        thread = threading.Thread(
            target=TelegramService.send_message_sync,
            args=(text, inline_keyboard, chat_id, "HTML", session_id),
            daemon=True
        )
        thread.start()

    @staticmethod
    def _extract_contact_info(text: str) -> Dict[str, Optional[str]]:
        """Extracts student name and phone/WhatsApp number from user message using regex."""
        if not text:
            return {"name": None, "phone": None}

        # Extract phone
        phone_match = re.search(r'(?:\+?57\s*)?(?:3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}|\b\d{7,10}\b)', text)
        phone = phone_match.group(0).strip() if phone_match else None

        # Extract name
        name = None
        name_match = re.search(r'(?:mi nombre es|me llamo|nombre[:\s]+|soy)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)', text, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
        else:
            words = [w for w in re.findall(r'[A-Za-zÀ-ÿ]+', text) if len(w) > 2]
            if 1 <= len(words) <= 3 and not re.match(r'^(hola|buenas|gracias|quiero|tienen|cuanto|como|que|donde|cuando|por|para|estoy|me|si|no|ok|vale)$', words[0], re.IGNORECASE):
                if not re.search(r'\d', text):
                    name = " ".join(words)

        return {"name": name, "phone": phone}

    @staticmethod
    def send_lead_alert(
        student_name: str,
        student_phone: str,
        program: str,
        user_message: str,
        session_id: str = "default"
    ) -> None:
        """Dispatches a rich Lead dossier alert to Telegram with action buttons."""
        clean_phone = student_phone.replace(" ", "").replace("+", "").replace("-", "")
        wa_phone = f"57{clean_phone}" if len(clean_phone) == 10 and clean_phone.startswith("3") else (clean_phone or "573000000000")
        wa_url = f"https://wa.me/{wa_phone}?text={urllib.parse.quote(f'Hola {student_name}, te contacto de Academia Lumina respecto a tu solicitud de {program}.')}"

        text = (
            "🎯 <b>NUEVO PROSPECTO REGISTRADO — ACADEMIA LUMINA</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Estudiante:</b> {student_name}\n"
            f"📱 <b>WhatsApp / Tel:</b> <code>{student_phone}</code>\n"
            f"📚 <b>Programa de Interés:</b> {program}\n"
            f"❓ <b>Inquietud / Consulta:</b>\n<i>« {user_message or 'Consulta general de matrícula'} »</i>\n"
            f"🆔 <b>ID Sesión:</b> <code>{session_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <b>Acciones de Atención:</b>"
        )

        keyboard = [
            [
                {"text": "💬 Abrir WhatsApp del Estudiante", "url": wa_url}
            ],
            [
                {"text": "🙋‍♂️ Tomar Caso", "callback_data": f"claim:{session_id}"},
                {"text": "✅ Caso Resuelto", "callback_data": f"resolve:{session_id}"}
            ]
        ]
        TelegramService.send_message_async(text, inline_keyboard=keyboard, session_id=session_id)

    @staticmethod
    def send_escalation_alert(
        user_message: str,
        assistant_response: str,
        session_id: str = "default",
        whatsapp_link: Optional[str] = None
    ) -> None:
        """Dispatches an out-of-scope human escalation alert with student contact and action buttons."""
        contact = TelegramService._extract_contact_info(user_message)
        student_name = contact["name"] or "Estudiante (por confirmar)"
        student_phone = contact["phone"] or "No registrado aún"

        clean_phone = re.sub(r'[^\d]', '', student_phone)
        if len(clean_phone) == 10 and clean_phone.startswith("3"):
            wa_num = f"57{clean_phone}"
        elif len(clean_phone) > 10:
            wa_num = clean_phone
        else:
            wa_num = None

        text = (
            "🚨 <b>NUEVO CASO ESCALADO — ACADEMIA LUMINA</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"❓ <b>Consulta no resuelta:</b>\n<i>« {user_message} »</i>\n\n"
            f"👤 <b>Estudiante:</b> {student_name}\n"
            f"📱 <b>WhatsApp / Tel:</b> <code>{student_phone}</code>\n"
            f"🆔 <b>ID de Sesión:</b> <code>{session_id}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👇 <b>Selecciona una acción para gestionar el caso:</b>"
        )

        keyboard = [
            [
                {"text": "🙋‍♂️ Tomar Caso", "callback_data": f"claim:{session_id}"},
                {"text": "✅ Caso Resuelto", "callback_data": f"resolve:{session_id}"}
            ]
        ]

        if wa_num:
            direct_wa = f"https://wa.me/{wa_num}?text={urllib.parse.quote(f'Hola {student_name}, te saludo de Academia Lumina. Respecto a tu consulta: \"{user_message}\"')}"
            keyboard.insert(0, [{"text": "💬 Abrir WhatsApp del Estudiante", "url": direct_wa}])
        elif whatsapp_link:
            keyboard.insert(0, [{"text": "📲 Abrir WhatsApp de Admisiones", "url": whatsapp_link}])

        TelegramService.send_message_async(text, inline_keyboard=keyboard, session_id=session_id)

    @staticmethod
    def send_student_live_message(session_id: str, message: str, conversation_id: int) -> None:
        """Forwards an incoming student live chat message to Telegram in real time."""
        text = (
            f"💬 <b>Mensaje de Estudiante en Vivo</b>\n"
            f"🆔 <b>Sesión:</b> <code>{session_id}</code>\n\n"
            f"<i>« {message} »</i>\n\n"
            "👉 <b>Responde directamente a este mensaje en Telegram</b> para contestarle al estudiante en la página web."
        )
        keyboard = [
            [
                {"text": "✅ Caso Resuelto", "callback_data": f"resolve:{session_id}"}
            ]
        ]
        TelegramService.send_message_async(text, inline_keyboard=keyboard, session_id=session_id)

    # =========================================================================
    # INBOUND TELEGRAM POLLER (BIDIRECTIONAL CHAT RUNNER)
    # =========================================================================

    @classmethod
    def start_polling(cls) -> None:
        """Starts background long-polling thread to receive advisor messages from Telegram."""
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            logger.info("[Telegram Poller] Bot token or chat ID not set. Polling disabled.")
            return

        if cls._polling_thread and cls._polling_thread.is_alive():
            return

        cls._stop_event.clear()
        cls._polling_thread = threading.Thread(target=cls._run_polling_loop, daemon=True)
        cls._polling_thread.start()
        logger.info("[Telegram Poller] Background polling thread started successfully.")

    @classmethod
    def stop_polling(cls) -> None:
        """Stops background polling."""
        cls._stop_event.set()

    @classmethod
    def _run_polling_loop(cls) -> None:
        while not cls._stop_event.is_set():
            try:
                payload = {
                    "timeout": 15,
                    "offset": cls._last_update_id + 1
                }
                res = cls._api_call("getUpdates", payload)
                if res and res.get("ok"):
                    for update in res.get("result", []):
                        cls._last_update_id = update["update_id"]
                        cls._handle_incoming_update(update)
            except Exception as e:
                logger.debug("[Telegram Poller Error]: %s", str(e))
                time.sleep(2)

    @classmethod
    def _handle_incoming_update(cls, update: Dict[str, Any]) -> None:
        from app.db.session import SessionLocal
        from app.db.repository import ConversationRepository
        from app.services.connection_manager import manager

        # 1. Handle Callback Query (Buttons clicked in Telegram)
        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb["id"]
            data = cb.get("data", "")
            from_user = cb.get("from", {}).get("first_name", "Asesor Telegram")
            
            if ":" in data:
                action, session_id = data.split(":", 1)
                with SessionLocal() as db:
                    conv = ConversationRepository.get_conversation_by_session_id(db, session_id)
                    if conv:
                        if action == "claim":
                            ConversationRepository.claim_conversation(db, conv.id, f"{from_user} (Telegram)")
                            # Notify student via WebSocket
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(manager.send_to_user(session_id, {
                                    "type": "agent_connected",
                                    "agent_name": f"{from_user} (Telegram)",
                                    "message": f"El asesor {from_user} se ha conectado desde Telegram para atenderte."
                                }))
                                loop.run_until_complete(manager.broadcast_to_agents({
                                    "type": "conversation_claimed",
                                    "conversation_id": conv.id,
                                    "session_id": session_id,
                                    "agent_username": f"{from_user} (Telegram)"
                                }))
                            finally:
                                loop.close()
                            cls._api_call("answerCallbackQuery", {
                                "callback_query_id": cb_id,
                                "text": "✅ Caso reclamado. Escribe tu mensaje para responderle al estudiante."
                            })
                            cls.send_message_sync(f"🎧 <b>Has tomado el caso de la sesión:</b> <code>{session_id}</code>.\nEscribe tu respuesta directamente aquí en Telegram.")

                        elif action == "resolve":
                            ConversationRepository.resolve_conversation(db, conv.id)
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(manager.send_to_user(session_id, {
                                    "type": "conversation_resolved",
                                    "message": "La conversación ha sido resuelta por el asesor. ¡Gracias por comunicarte con Academia Lumina!"
                                }))
                                loop.run_until_complete(manager.broadcast_to_agents({
                                    "type": "conversation_resolved",
                                    "conversation_id": conv.id,
                                    "session_id": session_id
                                }))
                            finally:
                                loop.close()
                            cls._api_call("answerCallbackQuery", {
                                "callback_query_id": cb_id,
                                "text": "✅ Caso resuelto exitosamente."
                            })
                            cls.send_message_sync(f"✅ <b>Conversación <code>{session_id}</code> marcada como resuelta.</b>")
            return

        # 2. Handle Text Message from Advisor
        if "message" in update and "text" in update["message"]:
            msg = update["message"]
            advisor_text = msg["text"].strip()
            sender_name = msg.get("from", {}).get("first_name", "Asesor")

            if advisor_text.startswith("/start") or advisor_text.startswith("/help"):
                cls.send_message_sync(
                    "🤖 <b>Academia Lumina — Asistente de Asesores</b>\n\n"
                    "Para responder a un estudiante:\n"
                    "1. Simplemente responde (Reply) al mensaje de alerta del estudiante en Telegram.\n"
                    "2. O usa el comando: <code>/responder [id_sesion] tu mensaje</code>\n"
                    "3. O usa los botones interactivos debajo de cada alerta."
                )
                return

            # Determine target session ID
            target_session_id = None
            if "reply_to_message" in msg:
                replied_msg_id = msg["reply_to_message"]["message_id"]
                target_session_id = cls._message_session_map.get(replied_msg_id)

            if not target_session_id and advisor_text.startswith("/responder"):
                parts = advisor_text.split(" ", 2)
                if len(parts) >= 3:
                    target_session_id = parts[1]
                    advisor_text = parts[2]

            if not target_session_id:
                # Fallback to most recent active session if only 1 active
                target_session_id = cls._active_session_id

            if not target_session_id:
                cls.send_message_sync("⚠️ No se identificó a qué estudiante responder. Por favor <b>responde (Reply)</b> a un mensaje de estudiante o usa <code>/responder [sesion] mensaje</code>.")
                return

            # Store in DB and dispatch via WebSockets to student browser and Admin Dashboard
            with SessionLocal() as db:
                conv = ConversationRepository.get_conversation_by_session_id(db, target_session_id)
                if not conv:
                    cls.send_message_sync(f"❌ Sesión <code>{target_session_id}</code> no encontrada en la base de datos.")
                    return

                # Auto claim if pending
                if conv.estado == "pendiente":
                    ConversationRepository.claim_conversation(db, conv.id, f"{sender_name} (Telegram)")

                # Save message in SQLite
                db_msg = ConversationRepository.add_message(db, conv.id, remitente="agent", contenido=advisor_text)

                # Send in real-time over WebSocket to student browser
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(manager.send_to_user(target_session_id, {
                        "type": "agent_message",
                        "sender": "agent",
                        "agent_name": f"{sender_name} (Asesor Telegram)",
                        "message": advisor_text,
                        "timestamp": db_msg.timestamp.isoformat()
                    }))
                    loop.run_until_complete(manager.broadcast_to_agents({
                        "type": "user_message",
                        "conversation_id": conv.id,
                        "session_id": target_session_id,
                        "message": advisor_text,
                        "estado": conv.estado,
                        "timestamp": db_msg.timestamp.isoformat()
                    }))
                finally:
                    loop.close()

                cls.send_message_sync(f"✅ <b>Mensaje enviado al estudiante en la web:</b>\n<i>« {advisor_text} »</i>")
