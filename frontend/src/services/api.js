/**
 * API Service Client for FastAPI Backend
 * Handles authenticated chat messages, admin JWT authentication,
 * document ingestion, metrics, and live agent handoff.
 */

const RAW_BACKEND_URL = import.meta.env.VITE_BACKEND_URL || (typeof window !== 'undefined' && window.location.hostname ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://localhost:8000');
export const API_BASE_URL = `${RAW_BACKEND_URL.replace(/\/$/, '')}/api/v1`;

// WebSocket Base URL
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

const API_KEY = import.meta.env.VITE_BACKEND_API_KEY || 'lumina_dev_api_key_2026';

// Admin Token Helpers
export function getAdminToken() {
  return localStorage.getItem('lumina_admin_token');
}

export function setAdminToken(token) {
  localStorage.setItem('lumina_admin_token', token);
}

export function getAdminRole() {
  return localStorage.getItem('lumina_admin_role') || 'asesor';
}

export function setAdminRole(role) {
  localStorage.setItem('lumina_admin_role', role);
}

export function getAdminFullName() {
  return localStorage.getItem('lumina_admin_fullname') || '';
}

export function setAdminFullName(name) {
  localStorage.setItem('lumina_admin_fullname', name || '');
}

export function removeAdminToken() {
  localStorage.removeItem('lumina_admin_token');
  localStorage.removeItem('lumina_admin_user');
  localStorage.removeItem('lumina_admin_role');
  localStorage.removeItem('lumina_admin_fullname');
}

export function getAdminUsername() {
  return localStorage.getItem('lumina_admin_user') || 'Admin';
}

export function setAdminUsername(username) {
  localStorage.setItem('lumina_admin_user', username);
}

function getAuthHeaders(includeContentType = true) {
  const headers = {};
  if (includeContentType) {
    headers['Content-Type'] = 'application/json';
  }
  const token = getAdminToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }
  return headers;
}

/**
 * Sends a user inquiry to the /chat FastAPI endpoint.
 */
export async function sendChatMessage(message, sessionId = 'default', language = 'en', history = []) {
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
 * Submits student lead contact information to /chat/lead.
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

/* ==========================================================================
   ADMIN & AGENT BACKOFFICE API
   ========================================================================== */

/**
 * Admin Login: validates username/password and stores JWT.
 */
export async function adminLogin(username, password) {
  const response = await fetch(`${API_BASE_URL}/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al iniciar sesión');
  }

  const data = await response.json();
  setAdminToken(data.access_token);
  setAdminUsername(data.username);
  setAdminRole(data.role || 'asesor');
  setAdminFullName(data.full_name || data.username);
  return data;
}

/**
 * Fetch current admin profile.
 */
export async function getAdminProfile() {
  const response = await fetch(`${API_BASE_URL}/admin/me`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Sesión no válida o expirada');
  }

  return await response.json();
}

/**
 * Fetch list of pending escalated conversations for agent inbox.
 */
export async function getPendingConversations() {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/pending`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Error al cargar conversaciones pendientes');
  }

  return await response.json();
}

/**
 * Fetch all conversations with optional state filter.
 */
export async function getAllConversations(estado = null) {
  const url = estado 
    ? `${API_BASE_URL}/admin/conversations?estado=${encodeURIComponent(estado)}` 
    : `${API_BASE_URL}/admin/conversations`;

  const response = await fetch(url, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Error al cargar conversaciones');
  }

  return await response.json();
}

/**
 * Fetch detailed conversation history with all messages.
 */
export async function getConversationDetail(conversationId) {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/${conversationId}`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al cargar detalle de conversación');
  }

  return await response.json();
}

/**
 * Agent claims a conversation.
 */
export async function claimConversation(conversationId) {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/${conversationId}/claim`, {
    method: 'POST',
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al reclamar conversación');
  }

  return await response.json();
}

/**
 * Agent marks a conversation as resolved.
 */
export async function resolveConversation(conversationId) {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/${conversationId}/resolve`, {
    method: 'POST',
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al resolver conversación');
  }

  return await response.json();
}

/**
 * Agent sends a real-time message to the student.
 */
export async function sendAgentMessage(conversationId, message) {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ message })
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al enviar mensaje');
  }

  return await response.json();
}

/**
 * Create a new conversation ticket (CRUD - Create).
 */
export async function createConversation(data) {
  const response = await fetch(`${API_BASE_URL}/admin/conversations`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al crear conversación');
  }

  return await response.json();
}

/**
 * Update conversation status / fields (CRUD - Update).
 */
export async function updateConversation(conversationId, data) {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/${conversationId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al actualizar conversación');
  }

  return await response.json();
}

/**
 * Delete a conversation (CRUD - Delete).
 */
export async function deleteConversation(conversationId) {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/${conversationId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al eliminar conversación');
  }

  return await response.json();
}

/**
 * Bulk delete multiple conversations.
 */
export async function bulkDeleteConversations(conversationIds) {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/bulk-delete`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ conversation_ids: conversationIds })
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al eliminar conversaciones');
  }

  return await response.json();
}

/**
 * Clear and purge all conversations from database (Admin cleanup).
 */
export async function clearAllConversations() {
  const response = await fetch(`${API_BASE_URL}/admin/conversations/clear-all`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al limpiar la base de datos');
  }

  return await response.json();
}

/**
 * List all knowledge base documents (PDF, DOCX, TXT, MD).
 */
export async function getDocuments() {
  const response = await fetch(`${API_BASE_URL}/admin/documents`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al obtener lista de documentos');
  }

  return await response.json();
}

/**
 * Upload a document (PDF, Word DOCX, TXT, MD) and trigger ChromaDB re-indexing.
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/admin/documents/upload`, {
    method: 'POST',
    headers: getAuthHeaders(false), // don't set Content-Type so browser sets boundary
    body: formData
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al subir e indexar documento');
  }

  return await response.json();
}

// Alias for backwards compatibility
export const uploadMarkdownDocument = uploadDocument;

/**
 * Delete a knowledge base document and remove its embeddings from ChromaDB.
 */
export async function deleteDocument(filename) {
  const response = await fetch(`${API_BASE_URL}/admin/documents/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al eliminar documento');
  }

  return await response.json();
}

/**
 * Fetch real system operational metrics.
 */
export async function getMetrics() {
  const response = await fetch(`${API_BASE_URL}/metrics`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    throw new Error('Error al obtener métricas del sistema');
  }

  return await response.json();
}

/**
 * Superadmin: Fetch list of all advisors/users.
 */
export async function getAdminUsers() {
  const response = await fetch(`${API_BASE_URL}/admin/users`, {
    headers: getAuthHeaders()
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al listar usuarios asesores');
  }

  return await response.json();
}

/**
 * Superadmin: Create a new advisor account.
 */
export async function createAdminUser(userData) {
  const response = await fetch(`${API_BASE_URL}/admin/users`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(userData)
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al crear cuenta de asesor');
  }

  return await response.json();
}

/**
 * Superadmin: Update advisor account role, status or password.
 */
export async function updateAdminUser(userId, userData) {
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(userData)
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Error al actualizar cuenta de asesor');
  }

  return await response.json();
}
