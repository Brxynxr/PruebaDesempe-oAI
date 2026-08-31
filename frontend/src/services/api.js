// Service helper para interactuar con la API backend de FastAPI

// In production (e.g. Render), VITE_BACKEND_URL is provided via environment variables.
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL
  ? `${import.meta.env.VITE_BACKEND_URL.replace(/\/$/, '')}/api/v1`
  : 'http://localhost:8000/api/v1';

const API_KEY = import.meta.env.VITE_BACKEND_API_KEY || 'lumina_secret_key_2026';

/**
 * Envia el mensaje del usuario al endpoint /chat de FastAPI adjuntando el header de seguridad X-API-Key e idioma.
 * @param {string} message - Pregunta del usuario
 * @param {string} sessionId - ID de sesión
 * @param {string} language - Idioma activo ('en' o 'es')
 * @returns {Promise<Object>} Respuesta estructurada del backend
 */
export async function sendChatMessage(message, sessionId = 'web_session_01', language = 'en') {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
        language: language
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

/**
 * Envía los datos del lead de estudiante (nombre, teléfono, programa) al endpoint /chat/lead de FastAPI.
 * @param {Object} leadData - Objeto con name, phone, program, user_message, session_id, language
 * @returns {Promise<Object>} Respuesta estructurada del backend
 */
export async function sendLeadInfo(leadData) {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/lead`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify(leadData)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error enviando lead:', error);
    throw error;
  }
}
