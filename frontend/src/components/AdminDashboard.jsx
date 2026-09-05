import React, { useState, useEffect, useRef } from 'react';
import { 
  Headphones, 
  FileUp, 
  BarChart3, 
  LogOut, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  UserCheck, 
  Send, 
  ArrowLeft, 
  MessageSquare, 
  CheckCheck,
  Globe,
  Sun,
  Moon,
  UploadCloud,
  FileText,
  DollarSign,
  Activity,
  Zap,
  Sparkles
} from 'lucide-react';
import { 
  getAdminUsername, 
  removeAdminToken, 
  getAdminToken,
  getPendingConversations, 
  getAllConversations, 
  getConversationDetail, 
  claimConversation, 
  resolveConversation, 
  sendAgentMessage, 
  uploadMarkdownDocument, 
  getMetrics,
  WS_BASE_URL 
} from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

export default function AdminDashboard({ onLogout, onBackToSite }) {
  const { language, toggleLanguage } = useLanguage();
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('inbox'); // 'inbox' | 'documents' | 'metrics'
  const adminName = getAdminUsername();

  // INBOX / LIVE CHAT STATE
  const [conversations, setConversations] = useState([]);
  const [selectedConvId, setSelectedConvId] = useState(null);
  const [activeConversation, setActiveConversation] = useState(null);
  const [agentInput, setAgentInput] = useState('');
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [filterStatus, setFilterStatus] = useState('pendiente'); // 'pendiente' | 'en_atencion' | 'all'
  const chatScrollRef = useRef(null);

  // DOCUMENT UPLOAD STATE
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [uploadError, setUploadError] = useState('');

  // METRICS STATE
  const [metrics, setMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  // WEBSOCKET FOR REAL-TIME AGENT CHANNEL
  useEffect(() => {
    const token = getAdminToken();
    if (!token) return;

    let socket;
    try {
      socket = new WebSocket(`${WS_BASE_URL}/ws/agent?token=${encodeURIComponent(token)}`);

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'new_escalation' || data.type === 'conversation_claimed' || data.type === 'conversation_resolved') {
            loadConversations();
            if (selectedConvId && data.conversation_id === selectedConvId) {
              loadConversationDetail(selectedConvId);
            }
          } else if (data.type === 'user_message') {
            if (selectedConvId && data.conversation_id === selectedConvId) {
              loadConversationDetail(selectedConvId);
            } else {
              loadConversations();
            }
          }
        } catch (err) {
          console.error('[Agent WS parse error]:', err);
        }
      };

      socket.onerror = (err) => {
        console.warn('[Agent WS Error]:', err);
      };
    } catch (e) {
      console.warn('[Agent WS Connection error]:', e);
    }

    return () => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [selectedConvId]);

  // Load conversations whenever tab or filter changes
  useEffect(() => {
    if (activeTab === 'inbox') {
      loadConversations();
    } else if (activeTab === 'metrics') {
      loadMetrics();
    }
  }, [activeTab, filterStatus]);

  const loadConversations = async () => {
    setLoadingConversations(true);
    try {
      let data;
      if (filterStatus === 'pendiente') {
        data = await getPendingConversations();
      } else if (filterStatus === 'en_atencion') {
        data = await getAllConversations('en_atencion');
      } else {
        data = await getAllConversations();
      }
      setConversations(data || []);
      // If currently selected conversation is not set and conversations exist, select the first
      if (!selectedConvId && data && data.length > 0) {
        setSelectedConvId(data[0].id);
        loadConversationDetail(data[0].id);
      }
    } catch (err) {
      console.error('Error loading conversations:', err);
    } finally {
      setLoadingConversations(false);
    }
  };

  const loadConversationDetail = async (convId) => {
    try {
      const detail = await getConversationDetail(convId);
      setActiveConversation(detail);
      setTimeout(() => {
        chatScrollRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      console.error('Error loading conversation detail:', err);
    }
  };

  const handleSelectConversation = (id) => {
    setSelectedConvId(id);
    loadConversationDetail(id);
  };

  const handleClaim = async () => {
    if (!selectedConvId) return;
    try {
      const updated = await claimConversation(selectedConvId);
      setActiveConversation(updated);
      loadConversations();
    } catch (err) {
      alert(err.message || 'Error al reclamar conversación');
    }
  };

  const handleResolve = async () => {
    if (!selectedConvId) return;
    try {
      const updated = await resolveConversation(selectedConvId);
      setActiveConversation(updated);
      loadConversations();
    } catch (err) {
      alert(err.message || 'Error al resolver conversación');
    }
  };

  const handleSendAgentMessage = async (e) => {
    e.preventDefault();
    if (!agentInput.trim() || !selectedConvId || sendingMessage) return;

    const text = agentInput.trim();
    setAgentInput('');
    setSendingMessage(true);
    try {
      await sendAgentMessage(selectedConvId, text);
      await loadConversationDetail(selectedConvId);
    } catch (err) {
      alert(err.message || 'Error al enviar mensaje');
    } finally {
      setSendingMessage(false);
    }
  };

  // DOCUMENT UPLOAD HANDLERS
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.md')) {
        setUploadError(language === 'es' ? 'Solo se permiten archivos .md' : 'Only .md files allowed');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setUploadError('');
      setUploadSuccess('');
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploadLoading(true);
    setUploadError('');
    setUploadSuccess('');

    try {
      const result = await uploadMarkdownDocument(selectedFile);
      setUploadSuccess(result.message || 'Documento reindexado con éxito.');
      setSelectedFile(null);
    } catch (err) {
      setUploadError(err.message || 'Error al procesar el archivo');
    } finally {
      setUploadLoading(false);
    }
  };

  // METRICS HANDLERS
  const loadMetrics = async () => {
    setLoadingMetrics(true);
    try {
      const data = await getMetrics();
      setMetrics(data);
    } catch (err) {
      console.error('Error fetching metrics:', err);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const handleLogoutClick = () => {
    removeAdminToken();
    onLogout();
  };

  return (
    <div className="admin-dashboard-container fade-in">
      {/* Top Admin Navigation Header */}
      <header className="admin-header glass-panel">
        <div className="admin-header-brand">
          <Sparkles className="gold-text" size={24} />
          <div className="admin-brand-texts">
            <h1 className="admin-brand-title">Academia Lumina Backoffice</h1>
            <span className="admin-logged-badge">
              <UserCheck size={13} />
              <span>{language === 'es' ? 'Asesor:' : 'Agent:'} <strong>{adminName}</strong></span>
            </span>
          </div>
        </div>

        {/* Tab Switcher */}
        <nav className="admin-tabs-nav">
          <button
            className={`admin-tab-btn ${activeTab === 'inbox' ? 'active' : ''}`}
            onClick={() => setActiveTab('inbox')}
          >
            <Headphones size={18} />
            <span>{language === 'es' ? 'Bandeja de Agentes' : 'Agent Inbox'}</span>
          </button>

          <button
            className={`admin-tab-btn ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            <FileUp size={18} />
            <span>{language === 'es' ? 'Documentos RAG' : 'RAG Documents'}</span>
          </button>

          <button
            className={`admin-tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('metrics')}
          >
            <BarChart3 size={18} />
            <span>{language === 'es' ? 'Métricas en Vivo' : 'Live Metrics'}</span>
          </button>
        </nav>

        {/* Controls: Language, Theme, Public Site & Logout */}
        <div className="admin-header-actions">
          <button 
            className="admin-icon-btn" 
            onClick={toggleLanguage}
            title={language === 'en' ? 'Cambiar a Español' : 'Switch to English'}
          >
            <Globe size={18} />
            <span className="btn-label-text">{language.toUpperCase()}</span>
          </button>

          <button 
            className="admin-icon-btn" 
            onClick={toggleTheme}
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={18} className="theme-icon-sun" /> : <Moon size={18} />}
          </button>

          <button 
            className="admin-secondary-btn" 
            onClick={onBackToSite}
            title="Ir al sitio público"
          >
            <ArrowLeft size={16} />
            <span>{language === 'es' ? 'Sitio Web' : 'Public Site'}</span>
          </button>

          <button 
            className="admin-logout-btn" 
            onClick={handleLogoutClick}
            title="Cerrar sesión"
          >
            <LogOut size={16} />
            <span>{language === 'es' ? 'Salir' : 'Logout'}</span>
          </button>
        </div>
      </header>

      {/* Main Backoffice Workspace */}
      <main className="admin-main-view">
        {/* ================================================================== */}
        {/* TAB 1: BANDEJA DE AGENTES & CHAT EN VIVO */}
        {/* ================================================================== */}
        {activeTab === 'inbox' && (
          <div className="admin-inbox-layout slide-up">
            {/* Left Column: Conversation Directory */}
            <div className="inbox-sidebar glass-panel">
              <div className="inbox-sidebar-header">
                <div className="inbox-filter-tabs">
                  <button
                    className={`filter-btn ${filterStatus === 'pendiente' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('pendiente')}
                  >
                    {language === 'es' ? 'Pendientes' : 'Pending'}
                  </button>
                  <button
                    className={`filter-btn ${filterStatus === 'en_atencion' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('en_atencion')}
                  >
                    {language === 'es' ? 'En Atención' : 'In Progress'}
                  </button>
                  <button
                    className={`filter-btn ${filterStatus === 'all' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('all')}
                  >
                    {language === 'es' ? 'Todas' : 'All'}
                  </button>
                </div>
                <button 
                  className="refresh-mini-btn" 
                  onClick={loadConversations} 
                  title="Refrescar"
                >
                  <RefreshCw size={14} className={loadingConversations ? 'spin' : ''} />
                </button>
              </div>

              <div className="inbox-list">
                {loadingConversations && conversations.length === 0 ? (
                  <div className="inbox-empty-state">
                    <p>{language === 'es' ? 'Cargando conversaciones...' : 'Loading conversations...'}</p>
                  </div>
                ) : conversations.length === 0 ? (
                  <div className="inbox-empty-state">
                    <CheckCheck size={32} className="gold-text" />
                    <p>{language === 'es' ? 'No hay conversaciones en esta bandeja.' : 'No conversations in this inbox.'}</p>
                  </div>
                ) : (
                  conversations.map((c) => (
                    <div
                      key={c.id}
                      className={`inbox-item ${selectedConvId === c.id ? 'selected' : ''} status-${c.estado}`}
                      onClick={() => handleSelectConversation(c.id)}
                    >
                      <div className="inbox-item-top">
                        <span className={`status-badge badge-${c.estado}`}>
                          {c.estado === 'pendiente' ? '⚠️ PENDIENTE' : c.estado === 'en_atencion' ? '🎧 EN ATENCIÓN' : c.estado === 'resuelto' ? '✅ RESUELTO' : '🤖 BOT'}
                        </span>
                        <span className="inbox-time">
                          <Clock size={12} />
                          {new Date(c.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="inbox-item-session">
                        <strong>ID:</strong> {c.session_id.substring(0, 18)}...
                      </div>
                      {c.last_message && (
                        <p className="inbox-last-msg">
                          "{c.last_message.length > 60 ? c.last_message.substring(0, 60) + '...' : c.last_message}"
                        </p>
                      )}
                      {c.agente_asignado && (
                        <div className="inbox-assigned">
                          <UserCheck size={12} />
                          <span>{c.agente_asignado}</span>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right Column: Active Live Chat with Full History */}
            <div className="inbox-chat-panel glass-panel">
              {activeConversation ? (
                <>
                  {/* Chat Top Action Bar */}
                  <div className="inbox-chat-header">
                    <div className="chat-header-info">
                      <div className="chat-title-row">
                        <MessageSquare size={18} className="gold-text" />
                        <h3>{language === 'es' ? 'Conversación' : 'Conversation'} #{activeConversation.id}</h3>
                        <span className={`status-badge badge-${activeConversation.estado}`}>
                          {activeConversation.estado.toUpperCase()}
                        </span>
                      </div>
                      <span className="session-id-subtitle">
                        Session: {activeConversation.session_id} • Idioma: {activeConversation.idioma.toUpperCase()}
                      </span>
                    </div>

                    <div className="chat-header-actions">
                      {activeConversation.estado === 'pendiente' && (
                        <button
                          className="btn-claim-chat pulse-glow"
                          onClick={handleClaim}
                        >
                          <Headphones size={16} />
                          <span>{language === 'es' ? 'Reclamar Conversación' : 'Claim Conversation'}</span>
                        </button>
                      )}

                      {activeConversation.estado === 'en_atencion' && (
                        <button
                          className="btn-resolve-chat"
                          onClick={handleResolve}
                        >
                          <CheckCircle size={16} />
                          <span>{language === 'es' ? 'Marcar como Resuelta' : 'Mark as Resolved'}</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Messages Feed */}
                  <div className="inbox-messages-feed">
                    <div className="history-divider">
                      <span>{language === 'es' ? 'Historial Completo con el Bot & Agente' : 'Full Bot & Agent History'}</span>
                    </div>

                    {activeConversation.messages && activeConversation.messages.map((m) => (
                      <div
                        key={m.id}
                        className={`admin-msg-row msg-${m.remitente}`}
                      >
                        <div className="admin-msg-bubble">
                          <div className="admin-msg-meta">
                            <span className="sender-tag">
                              {m.remitente === 'user' ? '👤 Estudiante' : m.remitente === 'agent' ? '🎧 Asesor' : '🤖 Bot IA'}
                            </span>
                            <span className="time-tag">
                              {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <div className="admin-msg-text">
                            {m.contenido}
                          </div>
                        </div>
                      </div>
                    ))}
                    <div ref={chatScrollRef} />
                  </div>

                  {/* Agent Reply Box */}
                  <form onSubmit={handleSendAgentMessage} className="inbox-reply-form">
                    <input
                      type="text"
                      className="inbox-reply-input"
                      placeholder={
                        activeConversation.estado === 'resuelto'
                          ? (language === 'es' ? 'Conversación resuelta.' : 'Conversation resolved.')
                          : (language === 'es' ? 'Escribe una respuesta al estudiante en tiempo real...' : 'Type a real-time message to the student...')
                      }
                      value={agentInput}
                      onChange={(e) => setAgentInput(e.target.value)}
                      disabled={activeConversation.estado === 'resuelto' || sendingMessage}
                    />
                    <button
                      type="submit"
                      className="inbox-send-btn"
                      disabled={!agentInput.trim() || activeConversation.estado === 'resuelto' || sendingMessage}
                    >
                      <Send size={18} />
                    </button>
                  </form>
                </>
              ) : (
                <div className="inbox-no-selected">
                  <MessageSquare size={48} className="gold-text" />
                  <h3>{language === 'es' ? 'Selecciona una conversación' : 'Select a conversation'}</h3>
                  <p>{language === 'es' ? 'Podrás ver el historial completo con el bot y responder en vivo.' : 'You can review the full bot history and reply in real time.'}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 2: SUBIDA DE DOCUMENTOS Y REINDEXACIÓN RAG */}
        {/* ================================================================== */}
        {activeTab === 'documents' && (
          <div className="admin-docs-view slide-up">
            <div className="admin-card-container glass-panel">
              <div className="admin-card-header">
                <UploadCloud size={32} className="gold-text" />
                <h2>{language === 'es' ? 'Carga y Reindexación de Base de Conocimiento' : 'Knowledge Base Upload & Re-indexing'}</h2>
                <p>
                  {language === 'es'
                    ? 'Sube archivos en formato Markdown (.md) para actualizar automáticamente la base vectorial en ChromaDB.'
                    : 'Upload Markdown (.md) documents to automatically update and re-index ChromaDB embeddings.'}
                </p>
              </div>

              {uploadSuccess && (
                <div className="admin-alert-success fade-in">
                  <CheckCircle size={20} />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              {uploadError && (
                <div className="admin-error-alert fade-in">
                  <AlertCircle size={20} />
                  <span>{uploadError}</span>
                </div>
              )}

              <form onSubmit={handleUploadSubmit} className="doc-upload-form">
                <div className="doc-dropzone">
                  <input
                    type="file"
                    id="docFileInput"
                    accept=".md"
                    onChange={handleFileChange}
                    className="file-input-hidden"
                  />
                  <label htmlFor="docFileInput" className="dropzone-label">
                    <FileText size={42} className="gold-text" />
                    <span className="dropzone-title">
                      {selectedFile ? selectedFile.name : (language === 'es' ? 'Haz clic para seleccionar un archivo .md' : 'Click to select a .md file')}
                    </span>
                    <span className="dropzone-subtitle">
                      {selectedFile 
                        ? `${(selectedFile.size / 1024).toFixed(1)} KB` 
                        : (language === 'es' ? 'Archivos de texto Markdown únicamente' : 'Markdown text files only')}
                    </span>
                  </label>
                </div>

                <button
                  type="submit"
                  className="btn-upload-submit pulse-glow"
                  disabled={!selectedFile || uploadLoading}
                >
                  {uploadLoading ? (
                    <span>{language === 'es' ? 'Reindexando ChromaDB...' : 'Re-indexing ChromaDB...'}</span>
                  ) : (
                    <>
                      <Zap size={18} />
                      <span>{language === 'es' ? 'Subir y Reindexar Base de Datos' : 'Upload & Re-index Knowledge Base'}</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 3: PANEL DE MÉTRICAS EN TIEMPO REAL */}
        {/* ================================================================== */}
        {activeTab === 'metrics' && (
          <div className="admin-metrics-view slide-up">
            <div className="metrics-header-row">
              <h2>{language === 'es' ? 'Métricas Operativas del Sistema' : 'System Operational Metrics'}</h2>
              <button 
                className="btn-refresh-metrics" 
                onClick={loadMetrics}
                disabled={loadingMetrics}
              >
                <RefreshCw size={16} className={loadingMetrics ? 'spin' : ''} />
                <span>{language === 'es' ? 'Actualizar Métricas' : 'Refresh Metrics'}</span>
              </button>
            </div>

            {loadingMetrics && !metrics ? (
              <div className="inbox-empty-state">
                <p>{language === 'es' ? 'Cargando métricas...' : 'Loading metrics...'}</p>
              </div>
            ) : metrics ? (
              <div className="metrics-cards-grid">
                <div className="metric-card glass-panel">
                  <div className="metric-card-top">
                    <span className="metric-label">{language === 'es' ? 'Consultas Totales' : 'Total Queries'}</span>
                    <Activity size={20} className="gold-text" />
                  </div>
                  <div className="metric-value">{metrics.total_queries}</div>
                  <div className="metric-footer">
                    {language === 'es' ? 'Interacciones procesadas' : 'Interactions processed'}
                  </div>
                </div>

                <div className="metric-card glass-panel">
                  <div className="metric-card-top">
                    <span className="metric-label">{language === 'es' ? 'Tasa de Caché' : 'Cache Hit Rate'}</span>
                    <Zap size={20} className="gold-text" />
                  </div>
                  <div className="metric-value">{metrics.cache_hit_rate_percentage}</div>
                  <div className="metric-footer">
                    {metrics.cached_queries} {language === 'es' ? 'respuestas desde caché' : 'cached responses'}
                  </div>
                </div>

                <div className="metric-card glass-panel">
                  <div className="metric-card-top">
                    <span className="metric-label">{language === 'es' ? 'Tasa de Escalamiento' : 'Escalation Rate'}</span>
                    <Headphones size={20} className="gold-text" />
                  </div>
                  <div className="metric-value">{metrics.escalation_rate_percentage}</div>
                  <div className="metric-footer">
                    {metrics.escalated_queries} {language === 'es' ? 'escaladas a asesor' : 'escalated to human'}
                  </div>
                </div>

                <div className="metric-card glass-panel">
                  <div className="metric-card-top">
                    <span className="metric-label">{language === 'es' ? 'Tokens Consumidos' : 'Total Tokens'}</span>
                    <DollarSign size={20} className="gold-text" />
                  </div>
                  <div className="metric-value">{metrics.total_tokens || metrics.total_tokens_estimated || 0}</div>
                  <div className="metric-footer">
                    {metrics.estimated_cost_usd}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </main>
    </div>
  );
}
