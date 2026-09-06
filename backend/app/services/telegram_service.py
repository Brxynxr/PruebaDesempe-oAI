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
        """Dispatches a clean, professional Lead dossier alert to Telegram with action buttons."""
        clean_phone = student_phone.replace(" ", "").replace("+", "").replace("-", "")
        wa_phone = f"57{clean_phone}" if len(clean_phone) == 10 and clean_phone.startswith("3") else (clean_phone or "573000000000")
        wa_url = f"https://wa.me/{wa_phone}?text={urllib.parse.quote(f'Hola {student_name}, te contacto de Academia Lumina respecto a tu solicitud de {program}.')}"

        inquiry_preview = (user_message or "Consulta general de matrícula").strip()
        if len(inquiry_preview) > 140:
            inquiry_preview = inquiry_preview[:137] + "..."

        text = (
            "<b>NUEVO PROSPECTO — LUMINA</b>\n\n"
            f"<b>Estudiante:</b> {student_name}\n"
            f"<b>WhatsApp:</b> <code>+{wa_phone}</code>\n"
            f"<b>Programa:</b> {program}\n"
            f"<b>Consulta:</b> <i>« {inquiry_preview} »</i>\n"
            f"<b>Sesión:</b> <code>{session_id}</code>"
        )

        keyboard = [
            [
                {"text": "Abrir WhatsApp", "url": wa_url}
            ],
            [
                {"text": "Tomar Caso", "callback_data": f"claim:{session_id}"},
                {"text": "Resolver", "callback_data": f"resolve:{session_id}"}
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
        """Dispatches a clean out-of-scope human escalation alert with student contact and action buttons."""
        contact = TelegramService._extract_contact_info(user_message)
        student_name = contact["name"] or "Estudiante (Web)"
        student_phone = contact["phone"] or "Por confirmar"

        clean_phone = re.sub(r'[^\d]', '', student_phone)
        if len(clean_phone) == 10 and clean_phone.startswith("3"):
            wa_num = f"57{clean_phone}"
        elif len(clean_phone) > 10:
            wa_num = clean_phone
        else:
            wa_num = None

        query_preview = user_message.strip()
        if len(query_preview) > 140:
            query_preview = query_preview[:137] + "..."

        text = (
            "<b>CASO ESCALADO — ATENCIÓN REQUERIDA</b>\n\n"
            f"<b>Estudiante:</b> {student_name}\n"
            f"<b>WhatsApp:</b> <code>{student_phone}</code>\n"
            f"<b>Consulta:</b> <i>« {query_preview} »</i>\n"
            f"<b>Sesión:</b> <code>{session_id}</code>"
        )

        keyboard = [
            [
                {"text": "Tomar Caso", "callback_data": f"claim:{session_id}"},
                {"text": "Resolver", "callback_data": f"resolve:{session_id}"}
            ]
        ]

        if wa_num:
            direct_wa = f"https://wa.me/{wa_num}?text={urllib.parse.quote(f'Hola {student_name}, te saludo de Academia Lumina. Respecto a tu consulta: \"{user_message}\"')}"
            keyboard.insert(0, [{"text": "Abrir WhatsApp", "url": direct_wa}])
        elif whatsapp_link:
            keyboard.insert(0, [{"text": "Abrir WhatsApp Admisiones", "url": whatsapp_link}])

        TelegramService.send_message_async(text, inline_keyboard=keyboard, session_id=session_id)

    @staticmethod
    def send_student_live_message(session_id: str, message: str, conversation_id: int) -> None:
        """Forwards an incoming student live chat message to Telegram in real time."""
        msg_preview = message.strip()
        if len(msg_preview) > 200:
            msg_preview = msg_preview[:197] + "..."

        text = (
            "<b>MENSAJE DE ESTUDIANTE (EN VIVO)</b>\n\n"
            f"<b>Sesión:</b> <code>{session_id}</code>\n"
            f"<b>Mensaje:</b> <i>« {msg_preview} »</i>"
        )
        keyboard = [
            [
                {"text": "Caso Resuelto", "callback_data": f"resolve:{session_id}"}
            ]
        ]
        TelegramService.send_message_async(text, inline_keyboard=keyboard, session_id=session_id)

    # =========================================================================
    # INBOUND TELEGRAM POLLER (BIDIRECTIONAL CHAT RUNNER)
    # =========================================================================

    @classmethod
    def start_polling(cls) -> None:
        """Starts background long-polling thread to receive advisor messages from Telegram."""
        if cls._polling_thread and cls._polling_thread.is_alive():
            return
        cls._stop_event.clear()
        cls._polling_thread = threading.Thread(target=cls._polling_worker, daemon=True)
        cls._polling_thread.start()
        logger.info("Telegram Poller daemon started.")

    @classmethod
    def stop_polling(cls) -> None:
        """Signals background poller to terminate."""
        cls._stop_event.set()
        logger.info("Telegram Poller daemon signaled to stop.")

    @classmethod
    def _polling_worker(cls) -> None:
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            logger.info("Telegram polling disabled (No bot token configured).")
            return

        logger.info("Telegram bidirectional poller listening for updates...")
        while not cls._stop_event.is_set():
            try:
                payload = {
                    "offset": cls._last_update_id + 1,
                    "timeout": 15,
                    "allowed_updates": ["message", "callback_query"]
                }
                res = cls._api_call("getUpdates", payload)
                if res and res.get("ok"):
                    updates: List[Dict[str, Any]] = res.get("result", [])
                    for update in updates:
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
                    if not conv:
                        cls._api_call("answerCallbackQuery", {
                            "callback_query_id": cb_id,
                            "text": "Conversación no encontrada en el sistema.",
                            "show_alert": True
                        })
                        return

                    if action == "claim":
                        tg_agent = f"{from_user} (Telegram)"

                        # Validation 1: Prevent taking an already resolved conversation
                        if conv.estado == "resuelto":
                            cls._api_call("answerCallbackQuery", {
                                "callback_query_id": cb_id,
                                "text": "⚠️ Este caso ya fue resuelto y cerrado. No se puede tomar.",
                                "show_alert": True
                            })
                            cls.send_message_sync(
                                f"<b>AVISO:</b> El caso (Sesión: <code>{session_id}</code>) ya fue marcado como <b>RESUELTO</b>. No es posible tomarlo."
                            )
                            return

                        # Validation 2: Prevent taking if already taken by another advisor
                        if conv.estado == "en_atencion" and conv.agente_asignado and conv.agente_asignado != tg_agent:
                            cls._api_call("answerCallbackQuery", {
                                "callback_query_id": cb_id,
                                "text": f"Este caso ya fue tomado por {conv.agente_asignado}.",
                                "show_alert": True
                            })
                            return

                        claimed_conv = ConversationRepository.claim_conversation(db, conv.id, tg_agent)
                        if not claimed_conv:
                            cls._api_call("answerCallbackQuery", {
                                "callback_query_id": cb_id,
                                "text": "No se pudo tomar el caso (ya atendido o resuelto).",
                                "show_alert": True
                            })
                            return

                        # Notify student via WebSocket
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(manager.send_to_user(session_id, {
                                "type": "agent_connected",
                                "agent_name": tg_agent,
                                "message": f"El asesor {from_user} se ha conectado desde Telegram para atenderte."
                            }))
                            loop.run_until_complete(manager.broadcast_to_agents({
                                "type": "conversation_claimed",
                                "conversation_id": conv.id,
                                "session_id": session_id,
                                "agent_username": tg_agent
                            }))
                        finally:
                            loop.close()
                        cls._api_call("answerCallbackQuery", {
                            "callback_query_id": cb_id,
                            "text": "Caso tomado exitosamente."
                        })
                        cls.send_message_sync(
                            f"<b>CASO ASIGNADO</b> (Sesión: <code>{session_id}</code>)\n"
                            "────────────────────────────\n"
                            f"Atendido por: {tg_agent}\n"
                            "Puedes responder citando el mensaje o usando <code>/responder</code>."
                        )

                    elif action == "resolve":
                        if conv.estado == "resuelto":
                            cls._api_call("answerCallbackQuery", {
                                "callback_query_id": cb_id,
                                "text": "Este caso ya se encuentra resuelto y cerrado.",
                                "show_alert": True
                            })
                            return

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
                            "text": "Caso resuelto exitosamente."
                        })
                        cls.send_message_sync(
                            f"<b>CASO RESUELTO</b> (Sesión: <code>{session_id}</code>)\n"
                            "────────────────────────────\n"
                            "Conversación finalizada y cerrada."
                        )
            return

        # 2. Handle Text Message from Advisor
        if "message" in update and "text" in update["message"]:
            msg = update["message"]
            advisor_text = msg["text"].strip()
            sender_name = msg.get("from", {}).get("first_name", "Asesor")

            if advisor_text.startswith("/start") or advisor_text.startswith("/help"):
                cls.send_message_sync(
                    "<b>ACADEMIA LUMINA — ASISTENTE DE ASESORES</b>\n"
                    "────────────────────────────\n"
                    "Instrucciones para responder a un estudiante:\n\n"
                    "1. <b>Reply (Responder):</b> Cita directamente la alerta del estudiante en este grupo.\n"
                    "2. <b>Comando:</b> <code>/responder [id_sesion] tu mensaje</code>\n"
                    "3. <b>Botones interactivos:</b> 'Tomar Caso' o 'Caso Resuelto'.\n\n"
                    "<i>Nota: Es obligatorio citar el mensaje original o indicar el ID de sesión para evitar enviar respuestas al estudiante equivocado.</i>"
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
                    target_session_id = parts[1].strip()
                    advisor_text = parts[2].strip()
                else:
                    cls.send_message_sync("<b>AVISO:</b> Formato incompleto. Usa: <code>/responder [id_sesion] tu mensaje</code>")
                    return

            if not target_session_id:
                cls.send_message_sync(
                    "<b>AVISO: DESTINATARIO NO IDENTIFICADO</b>\n"
                    "────────────────────────────\n"
                    "En este grupo hay múltiples casos activos y asesores. Para responderle a un estudiante:\n\n"
                    "• Haz <b>Reply (Responder)</b> a la alerta del estudiante, o\n"
                    "• Escribe <code>/responder [id_sesion] tu mensaje</code>.\n\n"
                    "<i>No se envió ningún mensaje a ningún estudiante.</i>"
                )
                return

            # Store in DB and dispatch via WebSockets to student browser and Admin Dashboard
            with SessionLocal() as db:
                conv = ConversationRepository.get_conversation_by_session_id(db, target_session_id)
                if not conv:
                    cls.send_message_sync(f"<b>AVISO:</b> Sesión <code>{target_session_id}</code> no encontrada en la base de datos.")
                    return

                # Check 1: Cannot send messages to resolved conversations
                if conv.estado == "resuelto":
                    cls.send_message_sync(f"<b>AVISO:</b> El caso de la sesión <code>{target_session_id}</code> ya está resuelto y cerrado. No se envió el mensaje.")
                    return

                tg_agent_name = f"{sender_name} (Telegram)"

                # Check 2: Cannot send messages if claimed by another advisor
                if conv.estado == "en_atencion" and conv.agente_asignado and conv.agente_asignado not in (tg_agent_name, sender_name, f"@{sender_name}"):
                    cls.send_message_sync(f"<b>AVISO:</b> Este caso ya está siendo atendido por '{conv.agente_asignado}'. No se envió el mensaje.")
                    return

                # Auto claim if pending
                if conv.estado == "pendiente":
                    ConversationRepository.claim_conversation(db, conv.id, tg_agent_name)

                # Save message in SQLite with sender audit
                db_msg = ConversationRepository.add_message(
                    db, 
                    conv.id, 
                    remitente="agent", 
                    contenido=advisor_text,
                    sender_username=tg_agent_name
                )

                # Send in real-time over WebSocket to student browser
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(manager.send_to_user(target_session_id, {
                        "type": "agent_message",
                        "sender": "agent",
                        "agent_name": tg_agent_name,
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

                cls.send_message_sync(
                    f"<b>RESPUESTA ENTREGADA AL ESTUDIANTE</b> (Sesión: <code>{target_session_id}</code>)\n"
                    "────────────────────────────\n"
                    f"<i>« {advisor_text} »</i>"
                )
