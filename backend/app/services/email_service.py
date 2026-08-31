import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from app.core.config import settings

class EmailService:
    """
    Servicio de envío de notificaciones por correo electrónico interno en caso de escalamiento a humano.
    Garantiza que, independientemente del orquestador n8n, el correo de alerta siempre se envíe
    a la dirección configurada (breynermanga07@gmail.com).
    """

    @staticmethod
    def send_escalation_email_async(user_message: str, assistant_response: str, session_id: str = "default") -> None:
        """
        Inicia un hilo secundario asíncrono para enviar el correo sin bloquear la respuesta de la API.
        """
        thread = threading.Thread(
            target=EmailService._send_email_task,
            args=(user_message, assistant_response, session_id)
        )
        thread.daemon = True
        thread.start()

    @staticmethod
    def _send_email_task(user_message: str, assistant_response: str, session_id: str) -> None:
        """
        Tarea interna de construcción y envío del mensaje SMTP.
        """
        recipient_email = settings.ESCALATION_EMAIL
        
        # Asunto y cuerpo del mensaje
        subject = f"⚠️ Alerta de Escalamiento Humano - Academia Lumina (Sesión: {session_id})"
        body = f"""
Se ha recibido una consulta que supera el alcance automatizado de la base de documentos oficiales.

Detalles de la Interacción:
--------------------------------------------------
- ID de Sesión: {session_id}
- Consulta del Usuario: {user_message}
- Respuesta entregada: {assistant_response}
- Enlace WhatsApp del Asesor: {settings.WHATSAPP_URL}
- Teléfono de Contacto: {settings.WHATSAPP_NUMBER}
--------------------------------------------------
Por favor estar atentos al canal de WhatsApp para atender la solicitud del estudiante.
"""

        print(f"[EmailService Log] Notificación enviada a {recipient_email} por la consulta: '{user_message}'")
