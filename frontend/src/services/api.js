// Service helper para interactuar con la API backend de FastAPI

const API_BASE_URL = 'http://localhost:8000/api/v1';
const API_KEY = 'lumina_secret_key_2026'; // Coincide con BACKEND_API_KEY en .env

/**
 * Envia el mensaje del usuario al endpoint /chat de FastAPI adjuntando el header de seguridad X-API-Key.
 * @param {string} message - Pregunta del usuario
 * @param {string} sessionId - ID de sesión
 * @returns {Promise<Object>} Respuesta estructurada del backend
 */
export async function sendChatMessage(message, sessionId = 'web_session_01') {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error en servicio de API:', error);
    throw error;
  }
}
