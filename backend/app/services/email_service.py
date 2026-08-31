import smtplib
import re
import urllib.parse
import html
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

logger = logging.getLogger("lumina.email")
from app.core.config import settings

class EmailService:
    """
    Servicio de envío de notificaciones por correo electrónico interno en caso de escalamiento a humano.
    Genera enlaces dinámicos de WhatsApp para que el asesor pueda responder al estudiante con un saludo pre-llenado.
    """

    @staticmethod
    def _clean_text_for_email(text: str) -> str:
        """
        Limpia símbolos de formato markdown (*, **, #, `) y saltos de línea crudos.
        """
        if not text:
            return ""
        cleaned = re.sub(r'\*+', '', text)
        cleaned = re.sub(r'#+\s*', '', cleaned)
        cleaned = re.sub(r'`+', '', cleaned)
        return cleaned.strip()

    @staticmethod
    def _format_whatsapp_number(phone: str) -> str:
        """
        Formatea el número de teléfono para asegurar el código de país (ej. Colombia +57).
        """
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10 and digits.startswith('3'):
            return f"57{digits}"
        return digits or "573247836387"

    @staticmethod
    def send_lead_email_async(
        student_name: str,
        student_phone: str,
        program: str,
        user_message: str,
        session_id: str = "default"
    ) -> None:
        """
        Inicia un hilo secundario asíncrono para enviar el correo con los datos del lead capturado en el chat.
        """
        thread = threading.Thread(
            target=EmailService._send_lead_email_task,
            args=(student_name, student_phone, program, user_message, session_id)
        )
        thread.daemon = True
        thread.start()

    @staticmethod
    def send_escalation_email_async(user_message: str, assistant_response: str, session_id: str = "default") -> None:
        """
        Fallback genérico de escalamiento asíncrono.
        """
        thread = threading.Thread(
            target=EmailService._send_email_task,
            args=(user_message, assistant_response, session_id)
        )
        thread.daemon = True
        thread.start()

    @staticmethod
    def _send_lead_email_task(
        student_name: str,
        student_phone: str,
        program: str,
        user_message: str,
        session_id: str
    ) -> None:
        """
        Construye y envía el correo al administrador con el botón hacia el WhatsApp del estudiante
        y el saludo prellenado para el asesor.
        """
        recipient_email = settings.ESCALATION_EMAIL
        sender_email = settings.SMTP_SENDER_EMAIL or settings.SMTP_USER or recipient_email

        clean_user_msg = EmailService._clean_text_for_email(user_message) or "Solicitud de asesoría sobre programas"
        clean_phone = EmailService._format_whatsapp_number(student_phone)

        safe_name = html.escape(student_name)
        safe_program = html.escape(program)
        safe_msg = html.escape(clean_user_msg)

        # Mensaje prellenado para el asesor (Cristiano Ronaldo) -> estudiante
        greeting_text = (
            f"Hola {student_name}, un gusto saludarte. Mi nombre es Cristiano Ronaldo, asesor de Academia Lumina, "
            f"y recibimos tu consulta sobre nuestro programa de {program}. "
            f"Respecto a tu solicitud: \"{clean_user_msg}\", ¿en qué te puedo colaborar hoy?"
        )
        encoded_greeting = urllib.parse.quote(greeting_text)
        student_whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_greeting}"

        # Asunto del correo
        subject = f"📥 Nuevo Lead de Estudiante: {student_name} - {program} (Sesión: {session_id})"

        # Cuerpo en texto plano (fallback)
        plain_body = f"""Se ha recibido una solicitud de contacto directo de un estudiante.

DATOS DEL ESTUDIANTE:
--------------------------------------------------
- Nombre Completo: {student_name}
- WhatsApp / Teléfono: +{clean_phone}
- Programa de Interés: {program}
- Consulta / Inquietud: {clean_user_msg}
- ID de Sesión: {session_id}
--------------------------------------------------
Enlace directo de contacto para el Asesor: {student_whatsapp_url}
"""

        # Cuerpo HTML minimalista en Oro Egipcio, Papiro y Negro Faraónico
        html_body = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nuevo Lead - Academia Lumina</title>
</head>
<body style="margin: 0; padding: 0; background-color: #fdfbf7; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #12100e;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #fdfbf7; padding: 30px 15px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(18, 16, 14, 0.08); border: 1px solid #e6dfd5;">
                    <!-- Encabezado -->
                    <tr>
                        <td style="background-color: #12100e; padding: 28px 30px; text-align: center; border-bottom: 2px solid #d4af37;">
                            <span style="background-color: #fef9c3; color: #854d0e; font-size: 11px; font-weight: 800; text-transform: uppercase; padding: 5px 14px; border-radius: 20px; letter-spacing: 1px; display: inline-block; margin-bottom: 10px;">👤 NUEVA SOLICITUD DE ASESORÍA</span>
                            <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 900; letter-spacing: -0.5px;">Academia Lumina</h1>
                        </td>
                    </tr>
                    <!-- Contenido Principal -->
                    <tr>
                        <td style="padding: 30px; background-color: #ffffff;">
                            <p style="font-size: 15px; line-height: 1.6; color: #4b5563; margin-top: 0;">
                                Se ha registrado un estudiante en el chat web que solicita atención personalizada por WhatsApp.
                            </p>
                            
                            <!-- Caja de Datos del Estudiante -->
                            <div style="background-color: #fdfbf7; border-left: 4px solid #d4af37; border-radius: 10px; padding: 20px; margin: 24px 0; border: 1px solid #e6dfd5;">
                                <h3 style="margin-top: 0; color: #12100e; font-size: 15px; border-bottom: 1px solid #e6dfd5; padding-bottom: 10px;">📋 Ficha del Estudiante</h3>
                                
                                <p style="margin: 8px 0; font-size: 14px; color: #12100e;"><strong>Estudiante:</strong> {safe_name}</p>
                                <p style="margin: 8px 0; font-size: 14px; color: #12100e;"><strong>WhatsApp:</strong> <a href="tel:+{clean_phone}" style="color: #b89228; text-decoration: none; font-weight: bold;">+{clean_phone}</a></p>
                                <p style="margin: 8px 0; font-size: 14px; color: #12100e;"><strong>Programa de Interés:</strong> <span style="background-color: #f5f0e6; padding: 3px 10px; border-radius: 12px; color: #b89228; font-weight: bold;">{safe_program}</span></p>
                                <p style="margin: 8px 0; font-size: 13px; color: #6e675f;"><strong>ID de Sesión:</strong> {session_id}</p>
                                
                                <p style="margin: 14px 0 6px 0; font-size: 13px; font-weight: bold; color: #12100e;">Consulta u Orientación Solicitada:</p>
                                <p style="margin: 0; padding: 12px 16px; background-color: #ffffff; border: 1px solid #e6dfd5; border-radius: 8px; font-size: 14px; color: #12100e; line-height: 1.5; font-style: italic;">
                                    "{safe_msg}"
                                </p>
                            </div>

                            <!-- Botón CTA WhatsApp Directo -->
                            <div style="text-align: center; margin: 28px 0 20px 0;">
                                <a href="{student_whatsapp_url}" target="_blank" style="background-color: #12100e; color: #d4af37; border: 1px solid #d4af37; font-size: 14px; font-weight: 800; text-decoration: none; padding: 14px 28px; border-radius: 30px; display: inline-block; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.25);">
                                    💬 Abrir Chat de WhatsApp con {safe_name}
                                </a>
                            </div>

                            <p style="font-size: 12px; color: #6e675f; text-align: center; margin: 0; font-style: italic;">
                                Al presionar el botón se abrirá el chat del estudiante con el mensaje de presentación listo para enviar.
                            </p>
                        </td>
                    </tr>
                    <!-- Pie de página -->
                    <tr>
                        <td style="background-color: #12100e; padding: 16px 30px; text-align: center; font-size: 12px; color: #a8a29e; border-top: 1px solid #2b2620;">
                            © 2026 Academia Lumina - Captura Inteligente de Leads RAG
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning(f"[EmailService Warning] No se enviará correo por SMTP. Lead registrado: '{student_name}' ({student_phone}).")
            return

        try:
            if settings.SMTP_PORT == 465:
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(sender_email, [recipient_email], msg.as_string())
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    if settings.SMTP_USE_TLS:
                        server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(sender_email, [recipient_email], msg.as_string())
            logger.info(f"[EmailService Success] Correo de lead enviado exitosamente a {recipient_email} para el estudiante: '{student_name}'")
        except Exception as e:
            logger.error(f"[EmailService Error] Error enviando correo de lead: {str(e)}")

    @staticmethod
    def _send_email_task(user_message: str, assistant_response: str, session_id: str) -> None:
        """
        Fallback genérico de escalamiento.
        """
        EmailService._send_lead_email_task(
            student_name="Estudiante Interesado",
            student_phone="3247836387",
            program="Idiomas General",
            user_message=user_message,
            session_id=session_id
        )
