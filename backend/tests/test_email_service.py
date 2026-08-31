import time
from unittest.mock import patch, MagicMock
from app.services.email_service import EmailService
from app.core.config import settings

def test_send_email_task_without_credentials():
    """
    Verifica que si no hay credenciales SMTP configuradas, el servicio no falle ni arroje excepciones.
    """
    with patch.object(settings, "SMTP_USER", ""), patch.object(settings, "SMTP_PASSWORD", ""):
        # No debe lanzar excepción
        EmailService._send_email_task(
            user_message="¿Tienen becas a Canadá?",
            assistant_response="No se encontró información.",
            session_id="test_session"
        )

@patch("smtplib.SMTP")
def test_send_email_task_with_credentials_smtp(mock_smtp):
    """
    Verifica que con credenciales válidas en puerto 587 se conecte, autentique y envíe el correo vía SMTP/STARTTLS.
    """
    mock_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_instance

    with patch.object(settings, "SMTP_HOST", "smtp.test.com"), \
         patch.object(settings, "SMTP_PORT", 587), \
         patch.object(settings, "SMTP_USER", "user@test.com"), \
         patch.object(settings, "SMTP_PASSWORD", "secret123"), \
         patch.object(settings, "SMTP_USE_TLS", True):

        EmailService._send_email_task(
            user_message="Consulta prueba",
            assistant_response="Respuesta prueba",
            session_id="s_test"
        )

        mock_smtp.assert_called_once_with("smtp.test.com", 587, timeout=10)
        mock_instance.starttls.assert_called_once()
        mock_instance.login.assert_called_once_with("user@test.com", "secret123")
        mock_instance.sendmail.assert_called_once()

def test_send_escalation_email_async():
    """
    Verifica que el método asíncrono inicie un hilo en segundo plano correctamente.
    """
    with patch.object(EmailService, "_send_email_task") as mock_task:
        EmailService.send_escalation_email_async("msg", "resp", "s1")
        time.sleep(0.2)
        mock_task.assert_called_once_with("msg", "resp", "s1")
