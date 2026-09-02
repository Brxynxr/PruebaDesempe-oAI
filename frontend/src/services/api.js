/**
 * API Service Client for FastAPI Backend
 * Handles authenticated chat messages and lead registration.
 */

// In production or Docker, VITE_BACKEND_URL is provided via environment variables
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL
  ? `${import.meta.env.VITE_BACKEND_URL.replace(/\/$/, '')}/api/v1`
  : 'http://localhost:8000/api/v1';

const API_KEY = import.meta.env.VITE_BACKEND_API_KEY || '';

/**
 * Sends a user inquiry to the /chat FastAPI endpoint with X-API-Key security header.
 * @param {string} message - User question or inquiry
 * @param {string} sessionId - Tracking session identifier
 * @param {string} language - Active interface language ('en' or 'es')
 * @returns {Promise<Object>} Structured response from the backend RAG engine
 */
export async function sendChatMessage(message, sessionId = 'web_session_01', language = 'en', history = []) {
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
        language: language,
        history: history
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('[API Service Error] sendChatMessage failed:', error);
    throw error;
  }
}

/**
 * Submits student lead contact information (name, phone, program) to /chat/lead.
 * @param {Object} leadData - Object containing name, phone, program, user_message, session_id, language
 * @returns {Promise<Object>} Confirmation payload from the backend
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
      throw new Error(errorData.detail || `HTTP Error ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('[API Service Error] sendLeadInfo failed:', error);
    throw error;
  }
}
