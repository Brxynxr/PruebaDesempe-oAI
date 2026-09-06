from app.services.telegram_service import TelegramService
from unittest.mock import patch

def test_telegram_rejects_untargeted_messages():
    """
    Verifica que mensajes de texto en Telegram sin reply ni /responder
    no adivinen el destinatario y sean rechazados cordialmente pidiendo clarificación.
    """
    with patch.object(TelegramService, "send_message_sync") as mock_send:
        # Simulate incoming message without reply_to_message and without /responder
        update = {
            "update_id": 99999,
            "message": {
                "message_id": 501,
                "text": "Hola estudiante, ya te atiendo",
                "from": {"first_name": "Carlos Asesor"}
            }
        }
        
        TelegramService._handle_incoming_update(update)
        
        # Verify send_message_sync was called with warning guidance
        assert mock_send.called
        sent_text = mock_send.call_args[0][0]
        assert "Destinatario no identificado" in sent_text or "Reply" in sent_text

def test_telegram_responder_command_with_session_id():
    """
    Verifica que el comando /responder [session_id] texto identifique la sesión.
    """
    with patch.object(TelegramService, "send_message_sync") as mock_send:
        # Valid command format
        update = {
            "update_id": 100000,
            "message": {
                "message_id": 502,
                "text": "/responder sesion_inexistente_999 Hola",
                "from": {"first_name": "Carlos Asesor"}
            }
        }
        TelegramService._handle_incoming_update(update)
        assert mock_send.called
        sent_text = mock_send.call_args[0][0]
        assert "no encontrada" in sent_text
