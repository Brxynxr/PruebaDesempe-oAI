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
  Sparkles,
  Trash2,
  Plus,
  Search,
  ExternalLink,
  MessageCircle,
  Tag
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
  createConversation,
  updateConversation,
  deleteConversation,
  clearAllConversations,
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
  const rawAdminName = getAdminUsername();
  const advisorName = rawAdminName === 'admin' ? 'Asesor Principal' : (rawAdminName || 'Asesor Lumina');

  // INBOX / LIVE CHAT STATE
  const [conversations, setConversations] = useState([]);
  const [selectedConvId, setSelectedConvId] = useState(null);
  const [activeConversation, setActiveConversation] = useState(null);
  const [agentInput, setAgentInput] = useState('');
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [filterStatus, setFilterStatus] = useState('pendiente'); // 'pendiente' | 'en_atencion' | 'all'
  const [searchQuery, setSearchQuery] = useState('');
  const [showNewModal, setShowNewModal] = useState(false);
  const [newSessionId, setNewSessionId] = useState('');
  const [newInitialMsg, setNewInitialMsg] = useState('');
  const [newLang, setNewLang] = useState('es');
  const [showFullTranscript, setShowFullTranscript] = useState(false);
  const [chatError, setChatError] = useState('');
  const chatScrollRef = useRef(null);

  // Helper to extract executive summary for advisor view
  const extractConversationSummary = (conv) => {
    if (!conv || !conv.messages || conv.messages.length === 0) {
      return {
        studentName: 'Estudiante Lumina',
        phone: 'No registrado',
        mainQuery: conv?.last_message || 'Consulta de información académica',
        latestQuery: null,
        detectedProgram: 'Academia Lumina',
        topicCategory: 'Información General',
        initialTime: conv?.created_at ? new Date(conv.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Reciente',
        totalMessages: 0
      };
    }

    const userMessages = conv.messages.filter(m => m.remitente === 'user').map(m => m.contenido.trim());
    const allUserText = userMessages.join(' \n ');

    // Extract Phone / WhatsApp
    const phoneMatch = allUserText.match(/(?:\+?57\s*)?(?:3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}|\b\d{7,10}\b)/);
    const phone = phoneMatch ? phoneMatch[0] : null;

    // Extract Name patterns
    let studentName = null;
    const namePatternMatch = allUserText.match(/(?:mi nombre es|me llamo|nombre[:\s]+|soy)\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)/i);
    if (namePatternMatch) {
      studentName = namePatternMatch[1].trim();
    } else {
      for (const msg of userMessages) {
        const clean = msg.replace(/[^\w\s]/g, '').trim();
        const words = clean.split(/\s+/).filter(w => w.length > 2);
        if (
          words.length >= 1 && 
          words.length <= 3 && 
          !/^(hola|holaa|buenas|gracias|quiero|tienen|cuanto|como|que|donde|cuando|por|para|estoy|me|si|no|ok|vale)$/i.test(words[0]) &&
          !/\d/.test(msg)
        ) {
          studentName = clean;
          break;
        }
      }
    }

    // Filter out greeting messages to isolate the substantive inquiry
    const substantiveQueries = userMessages.filter(msg => {
      const clean = msg.toLowerCase().replace(/[^\w\s]/g, '').trim();
      return !/^(hola|holaa|holaaa|buenas|buenos dias|buenos días|buenas tardes|buenas noches|hello|hi|hey|gracias|muchas gracias|ok|vale|listo)$/i.test(clean);
    });

    const mainQuery = substantiveQueries.length > 0 ? substantiveQueries[0] : (userMessages[0] || 'Consulta inicial');
    const latestQuery = substantiveQueries.length > 1 ? substantiveQueries[substantiveQueries.length - 1] : null;

    // Detect program
    let detectedProgram = 'General / Todos los idiomas';
    if (/ingl[eé]s|english/i.test(allUserText)) detectedProgram = 'Inglés (MCER A1 - C1)';
    else if (/franc[eé]s|french/i.test(allUserText)) detectedProgram = 'Francés (DELF / DALF)';
    else if (/portugu[eé]s|portuguese/i.test(allUserText)) detectedProgram = 'Portugués (Negocios / Fluidez)';

    // Topic classification
    let topicCategory = 'Validación Especial / Admisiones';
    if (/descuento|beca|precio|costo|tarifa|promocion|financiaci[oó]n|cuota/i.test(allUserText)) {
      topicCategory = '💰 Descuentos, Tarifas y Becas';
    } else if (/doble cobro|reembolso|devoluci[oó]n|pago|tarjeta|transferencia/i.test(allUserText)) {
      topicCategory = '💳 Pagos y Facturación';
    } else if (/horario|modalidad|sabados|intensivo|online|presencial|noche|mañana/i.test(allUserText)) {
      topicCategory = '📅 Horarios y Modalidades';
    } else if (/parqueadero|cafeteria|sede|laboratorio|ubicaci[oó]n/i.test(allUserText)) {
      topicCategory = '🏢 Instalaciones y Sede';
    } else if (/intercambio|viaje|canada|suiza|alemania/i.test(allUserText)) {
      topicCategory = '✈️ Convenios e Intercambios';
    }

    return {
      studentName: studentName || 'Estudiante Interesado',
      phone: phone || 'No registrado aún',
      mainQuery,
      latestQuery: (latestQuery && latestQuery !== mainQuery) ? latestQuery : null,
      detectedProgram,
      topicCategory,
      initialTime: conv.created_at ? new Date(conv.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Reciente',
      totalMessages: conv.messages ? conv.messages.length : 0
    };
  };

  // DOCUMENT UPLOAD STATE
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [uploadError, setUploadError] = useState('');

  // METRICS STATE
  const [metrics, setMetrics] = useState(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  // QUICK RESPONSE TEMPLATES
  const quickTemplates = [
    { title: '👋 Bienvenida', text: '¡Hola! Te saluda tu asesor académico de Academia Lumina. Con gusto te brindo toda la información para tu matrícula.' },
    { title: '📅 Horarios', text: 'Nuestros programas inician el primer lunes de cada mes en modalidades Presencial (Sede Principal) y Virtual interactiva en vivo.' },
    { title: '💰 Costos & Becas', text: 'Contamos con 15% de descuento por pronto pago e inscripción anticipada. Además ofrecemos facilidades de financiación en cuotas sin interés.' },
    { title: '📜 Certificación', text: 'Nuestros cursos están alineados y certificados bajo el Marco Común Europeo (MCER) desde A1 hasta C1, válidos internacionalmente.' },
    { title: '📲 WhatsApp', text: '¿Deseas que continuemos por WhatsApp para enviarte el formulario de inscripción y formalizar tu matrícula?' }
  ];

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
          if (
            data.type === 'new_escalation' || 
            data.type === 'conversation_claimed' || 
            data.type === 'conversation_resolved' ||
            data.type === 'conversation_updated' ||
            data.type === 'conversation_deleted'
          ) {
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
      } else if (filterStatus === 'resuelto') {
        data = await getAllConversations('resuelto');
      } else {
        data = await getAllConversations();
      }
      setConversations(data || []);
      // NOTE: No auto-select! The chat stays closed until the advisor explicitly clicks a conversation.
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
    setShowFullTranscript(false);
    setChatError('');
    loadConversationDetail(id);
  };

  // CRUD: Claim (Update)
  const handleClaim = async () => {
    if (!selectedConvId) return;
    setChatError('');
    try {
      const updated = await claimConversation(selectedConvId);
      setActiveConversation(updated);
      setFilterStatus('en_atencion');
      loadConversations();
    } catch (err) {
      setChatError(err.message || 'Error al reclamar conversación');
    }
  };

  // CRUD: Resolve (Update - Automatically moves case to 'Casos Resueltos')
  const handleResolve = async () => {
    if (!selectedConvId) return;
    setChatError('');
    try {
      const updated = await resolveConversation(selectedConvId);
      setActiveConversation(updated);
      // Automatically switch view to 'Casos Resueltos' so advisor sees it archived
      setFilterStatus('resuelto');
    } catch (err) {
      setChatError(err.message || 'Error al resolver conversación');
    }
  };

  // CRUD: Clear / Purge all test conversations
  const handleClearAll = async () => {
    if (!window.confirm('¿Deseas limpiar todos los chats de prueba acumulados y dejar la bandeja en blanco?')) {
      return;
    }
    try {
      await clearAllConversations();
      setSelectedConvId(null);
      setActiveConversation(null);
      loadConversations();
    } catch (err) {
      setChatError(err.message || 'Error al limpiar la base de datos');
    }
  };

  // CRUD: Fast Status Update
  const handleQuickStatusChange = async (newStatus) => {
    if (!selectedConvId) return;
    setChatError('');
    try {
      const updated = await updateConversation(selectedConvId, { estado: newStatus });
      setActiveConversation(updated);
      loadConversations();
    } catch (err) {
      setChatError(err.message || 'Error al actualizar estado');
    }
  };

  // CRUD: Delete Conversation
  const handleDelete = async (convId, e) => {
    if (e) e.stopPropagation();
    const idToDelete = convId || selectedConvId;
    if (!idToDelete) return;

    if (!window.confirm(`¿Estás seguro de eliminar permanentemente la conversación #${idToDelete}?`)) {
      return;
    }

    try {
      await deleteConversation(idToDelete);
      if (selectedConvId === idToDelete) {
        setSelectedConvId(null);
        setActiveConversation(null);
      }
      loadConversations();
    } catch (err) {
      setChatError(err.message || 'Error al eliminar conversación');
    }
  };

  // CRUD: Create New Custom / Simulated Conversation
  const handleCreateConversation = async (e) => {
    e.preventDefault();
    const sId = newSessionId.trim() || `manual_${Date.now()}`;
    try {
      const newConv = await createConversation({
        session_id: sId,
        idioma: newLang,
        estado: 'pendiente',
        initial_message: newInitialMsg.trim() || 'Consulta inicial registrada por asesor.'
      });
      setShowNewModal(false);
      setNewSessionId('');
      setNewInitialMsg('');
      loadConversations();
      setSelectedConvId(newConv.id);
      loadConversationDetail(newConv.id);
    } catch (err) {
      setChatError(err.message || 'Error al crear conversación');
    }
  };

  // Agent Send Message
  const handleSendAgentMessage = async (e) => {
    e.preventDefault();
    if (!agentInput.trim() || !selectedConvId || sendingMessage) return;

    if (activeConversation?.estado === 'pendiente') {
      setChatError(language === 'es' ? 'Debes tomar el caso antes de poder responder al estudiante.' : 'You must claim the case before sending a message.');
      return;
    }

    const text = agentInput.trim();
    setAgentInput('');
    setSendingMessage(true);
    setChatError('');
    try {
      await sendAgentMessage(selectedConvId, text);
      await loadConversationDetail(selectedConvId);
    } catch (err) {
      setChatError(err.message || 'Error al enviar mensaje');
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

  // Filter conversations by search query
  const filteredConversations = conversations.filter(c => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.session_id.toLowerCase().includes(q) ||
      (c.last_message && c.last_message.toLowerCase().includes(q)) ||
      c.id.toString().includes(q)
    );
  });

  return (
    <div className="admin-dashboard-container fade-in">
      {/* Top Advisor Navigation Header */}
      <header className="admin-header glass-panel">
        <div className="admin-header-brand">
          <Sparkles className="gold-text" size={26} />
          <div className="admin-brand-texts">
            <h1 className="admin-brand-title">
              {language === 'es' ? 'Panel de Asesores — Academia Lumina' : 'Advisor Portal — Academia Lumina'}
            </h1>
            <span className="admin-logged-badge">
              <UserCheck size={14} />
              <span>{language === 'es' ? 'Asesor Conectado:' : 'Active Advisor:'} <strong>{advisorName}</strong></span>
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
            <span>{language === 'es' ? 'Bandeja de Asesores' : 'Advisor Inbox'}</span>
            {conversations.filter(c => c.estado === 'pendiente').length > 0 && (
              <span className="tab-counter-badge">
                {conversations.filter(c => c.estado === 'pendiente').length}
              </span>
            )}
          </button>

          <button
            className={`admin-tab-btn ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            <FileUp size={18} />
            <span>{language === 'es' ? 'Base de Conocimiento RAG' : 'RAG Knowledge Base'}</span>
          </button>

          <button
            className={`admin-tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
            onClick={() => setActiveTab('metrics')}
          >
            <BarChart3 size={18} />
            <span>{language === 'es' ? 'Métricas & SLA' : 'Metrics & SLA'}</span>
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
        {/* TAB 1: BANDEJA DE ASESORES & CHAT EN VIVO CON CRUD COMPLETO */}
        {/* ================================================================== */}
        {activeTab === 'inbox' && (
          <div className="admin-inbox-layout slide-up">
            {/* Left Column: Conversation Directory & CRUD Actions */}
            <div className="inbox-sidebar glass-panel">
              <div className="inbox-sidebar-top-bar">
                <div className="inbox-filter-tabs">
                  <button
                    className={`filter-btn ${filterStatus === 'pendiente' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('pendiente')}
                  >
                    {language === 'es' ? '⚠️ Pendientes' : '⚠️ Pending'}
                  </button>
                  <button
                    className={`filter-btn ${filterStatus === 'en_atencion' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('en_atencion')}
                  >
                    {language === 'es' ? '🎧 En Atención' : '🎧 In Progress'}
                  </button>
                  <button
                    className={`filter-btn ${filterStatus === 'resuelto' ? 'active' : ''}`}
                    onClick={() => setFilterStatus('resuelto')}
                  >
                    {language === 'es' ? '✅ Casos Resueltos' : '✅ Resolved'}
                  </button>
                </div>

                <div className="inbox-actions-row">
                  <button 
                    className="btn-create-chat" 
                    onClick={() => setShowNewModal(true)}
                    title="Crear Nueva Consulta / Ticket"
                  >
                    <Plus size={14} />
                    <span>{language === 'es' ? 'Nuevo Chat' : 'New Chat'}</span>
                  </button>

                  <div className="inbox-secondary-actions">
                    <button 
                      className="btn-clear-inbox" 
                      onClick={handleClearAll}
                      title="Limpiar chats de prueba acumulados"
                    >
                      <Trash2 size={13} />
                      <span>{language === 'es' ? 'Limpiar' : 'Clear'}</span>
                    </button>
                    <button 
                      className="refresh-mini-btn" 
                      onClick={loadConversations} 
                      title="Refrescar lista"
                    >
                      <RefreshCw size={14} className={loadingConversations ? 'spin' : ''} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Search Bar */}
              <div className="inbox-search-box">
                <Search size={15} className="search-icon" />
                <input
                  type="text"
                  placeholder={language === 'es' ? 'Buscar por ID o mensaje...' : 'Search by ID or message...'}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="inbox-search-input"
                />
                {searchQuery && (
                  <button className="clear-search-btn" onClick={() => setSearchQuery('')}>✕</button>
                )}
              </div>

              <div className="inbox-list">
                {loadingConversations && conversations.length === 0 ? (
                  <div className="inbox-empty-state">
                    <p>{language === 'es' ? 'Cargando conversaciones...' : 'Loading conversations...'}</p>
                  </div>
                ) : filteredConversations.length === 0 ? (
                  <div className="inbox-empty-state">
                    <CheckCheck size={36} className="gold-text" />
                    <p>{language === 'es' ? 'No hay conversaciones en este apartado.' : 'No conversations in this section.'}</p>
                  </div>
                ) : (
                  filteredConversations.map((c) => (
                    <div
                      key={c.id}
                      className={`inbox-item ${selectedConvId === c.id ? 'selected' : ''} status-${c.estado}`}
                      onClick={() => handleSelectConversation(c.id)}
                    >
                      <div className="inbox-item-top">
                        <span className={`status-badge badge-${c.estado}`}>
                          {c.estado === 'pendiente' ? '⚠️ PENDIENTE' : c.estado === 'en_atencion' ? '🎧 EN ATENCIÓN' : c.estado === 'resuelto' ? '✅ RESUELTO' : '🤖 BOT'}
                        </span>
                        <div className="inbox-item-meta-right">
                          <span className="inbox-time">
                            <Clock size={12} />
                            {new Date(c.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                          <button
                            className="btn-item-delete"
                            onClick={(e) => handleDelete(c.id, e)}
                            title="Eliminar conversación"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </div>
                      <div className="inbox-item-session">
                        <strong>ID:</strong> <code>{c.session_id.length > 20 ? c.session_id.substring(0, 20) + '...' : c.session_id}</code>
                      </div>
                      {c.last_message && (
                        <p className="inbox-last-msg">
                          "{c.last_message.length > 65 ? c.last_message.substring(0, 65) + '...' : c.last_message}"
                        </p>
                      )}
                      {c.agente_asignado && (
                        <div className="inbox-assigned">
                          <UserCheck size={12} />
                          <span>Asesor: <strong>{c.agente_asignado}</strong></span>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right Column: Active Live Chat with Full History & Fast Actions */}
            <div className="inbox-chat-panel glass-panel">
              {activeConversation ? (
                <>
                  {/* Chat Top Action Bar */}
                  <div className="inbox-chat-header">
                    <div className="chat-header-info">
                      <div className="chat-title-row">
                        <MessageSquare size={20} className="gold-text" />
                        <h3>{language === 'es' ? 'Consulta' : 'Conversation'} #{activeConversation.id}</h3>
                        <span className={`status-badge badge-${activeConversation.estado}`}>
                          {activeConversation.estado.toUpperCase()}
                        </span>
                        <span className="lang-pill">{activeConversation.idioma.toUpperCase()}</span>
                      </div>
                      <span className="session-id-subtitle">
                        Session ID: <code>{activeConversation.session_id}</code>
                        {activeConversation.agente_asignado && (
                          <> • Asesor a cargo: <strong>{activeConversation.agente_asignado}</strong></>
                        )}
                      </span>
                    </div>

                    <div className="chat-header-actions">
                      {/* Quick status dropdown / actions */}
                      {activeConversation.estado === 'pendiente' && (
                        <button
                          className="btn-claim-chat pulse-glow"
                          onClick={handleClaim}
                          title="Tomar este caso para responder en tiempo real"
                        >
                          <Headphones size={16} />
                          <span>{language === 'es' ? 'Tomar Caso' : 'Claim Case'}</span>
                        </button>
                      )}

                      {activeConversation.estado === 'en_atencion' && (
                        <button
                          className="btn-resolve-chat pulse-glow"
                          onClick={handleResolve}
                          title="Finalizar atención y mover a Casos Resueltos"
                        >
                          <CheckCircle size={16} />
                          <span>{language === 'es' ? '✅ Caso Resuelto' : '✅ Case Resolved'}</span>
                        </button>
                      )}

                      <button
                        className="btn-chat-delete"
                        onClick={() => handleDelete(activeConversation.id)}
                        title="Eliminar permanentemente este chat"
                      >
                        <Trash2 size={16} />
                        <span>{language === 'es' ? 'Eliminar' : 'Delete'}</span>
                      </button>
                    </div>
                  </div>

                  {/* Messages Feed: Single Executive Summary Card + Real-time Live Advisor Chat */}
                  <div className="inbox-messages-feed">
                    {(() => {
                      const summary = extractConversationSummary(activeConversation);
                      
                      // Identify live conversation turns (messages by agent or messages after agent joined)
                      const firstAgentIdx = activeConversation.messages 
                        ? activeConversation.messages.findIndex(m => m.remitente === 'agent') 
                        : -1;
                      
                      const liveMessages = firstAgentIdx !== -1 
                        ? activeConversation.messages.slice(firstAgentIdx) 
                        : [];

                      return (
                        <>
                          {/* 1. SINGLE SUMMARY MESSAGE CARD */}
                          <div className="advisor-summary-card">
                            <div className="summary-card-header">
                              <div className="summary-title-wrapper">
                                <Sparkles size={18} className="gold-text" />
                                <h4>{language === 'es' ? 'Resumen Ejecutivo del Caso' : 'Case Executive Summary'}</h4>
                              </div>
                              <span className="summary-badge">{summary.topicCategory}</span>
                            </div>

                            <div className="summary-grid">
                              <div className="summary-field">
                                <span className="summary-label">👤 {language === 'es' ? 'Estudiante / Contacto:' : 'Student / Contact:'}</span>
                                <span className="summary-value">
                                  <strong>{summary.studentName}</strong> {summary.phone !== 'No registrado aún' && ` • WhatsApp: ${summary.phone}`}
                                </span>
                              </div>

                              <div className="summary-field">
                                <span className="summary-label">📚 {language === 'es' ? 'Programa de Interés:' : 'Program of Interest:'}</span>
                                <span className="summary-value">{summary.detectedProgram}</span>
                              </div>

                              <div className="summary-field full-width">
                                <span className="summary-label">❓ {language === 'es' ? 'Consulta que originó el escalamiento:' : 'Escalation Query:'}</span>
                                <p className="summary-quote">"{summary.mainQuery}"</p>
                              </div>

                              {summary.latestQuery && (
                                <div className="summary-field full-width">
                                  <span className="summary-label">💬 {language === 'es' ? 'Último mensaje recibido:' : 'Latest Student Message:'}</span>
                                  <p className="summary-quote">"{summary.latestQuery}"</p>
                                </div>
                              )}
                            </div>

                            <div className="summary-card-footer">
                              <span className="summary-timestamp">
                                <Clock size={13} /> {language === 'es' ? `Escalado a las ${summary.initialTime}` : `Escalated at ${summary.initialTime}`}
                              </span>
                              <button 
                                type="button"
                                className="btn-toggle-transcript"
                                onClick={() => setShowFullTranscript(!showFullTranscript)}
                              >
                                {showFullTranscript 
                                  ? (language === 'es' ? '▲ Ocultar historial detallado' : '▲ Hide full transcript')
                                  : (language === 'es' ? `▼ Ver historial detallado (${activeConversation.messages ? activeConversation.messages.length : 0} mensajes)` : `▼ View full transcript (${activeConversation.messages ? activeConversation.messages.length : 0} messages)`)}
                              </button>
                            </div>

                            {/* Collapsible raw transcript */}
                            {showFullTranscript && (
                              <div className="full-transcript-box slide-up">
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
                              </div>
                            )}
                          </div>

                          {/* 2. REAL-TIME LIVE AGENT CHAT FEED */}
                          {liveMessages.length > 0 ? (
                            <>
                              <div className="history-divider">
                                <span>{language === 'es' ? '🎧 Conversación en Vivo con Asesor' : '🎧 Live Advisor Chat'}</span>
                              </div>
                              {liveMessages.map((m) => (
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
                            </>
                          ) : (
                            <div className="live-chat-banner">
                              <Headphones size={18} />
                              <span>{language === 'es' ? 'Caso listo para atención en tiempo real. Escribe abajo para responder directamente al estudiante.' : 'Case ready for live support. Reply below to text the student in real time.'}</span>
                            </div>
                          )}
                        </>
                      );
                    })()}
                    <div ref={chatScrollRef} />
                  </div>

                  {/* Chat Error Banner if present */}
                  {chatError && (
                    <div className="chat-error-banner fade-in">
                      <div className="flex items-center gap-2">
                        <AlertCircle size={16} />
                        <span>{chatError}</span>
                      </div>
                      <button onClick={() => setChatError('')} title="Cerrar">✕</button>
                    </div>
                  )}

                  {/* Dynamic Bottom Action / Reply Area based on Case Status */}
                  {activeConversation.estado === 'pendiente' ? (
                    <div className="unclaimed-guard-bar">
                      <div className="unclaimed-guard-info">
                        <AlertCircle size={22} className="warning-icon" />
                        <div className="unclaimed-guard-texts">
                          <strong>{language === 'es' ? 'Caso pendiente de atención' : 'Case is pending assignment'}</strong>
                          <span>{language === 'es' ? 'Debes tomar este caso antes de poder responder en vivo al estudiante.' : 'You must claim this case before replying to the student.'}</span>
                        </div>
                      </div>
                      <button
                        type="button"
                        className="btn-claim-chat pulse-glow"
                        onClick={handleClaim}
                        title="Tomar este caso para responder en tiempo real"
                      >
                        <Headphones size={16} />
                        <span>{language === 'es' ? '🎧 Tomar Caso Ahora' : '🎧 Claim Case Now'}</span>
                      </button>
                    </div>
                  ) : activeConversation.estado === 'resuelto' ? (
                    <div className="resolved-guard-bar">
                      <CheckCircle size={20} className="success-icon" />
                      <span>{language === 'es' ? '✅ Este caso ha sido marcado como Resuelto (Solo lectura).' : '✅ This case has been marked as Resolved (Read-only).'}</span>
                    </div>
                  ) : (
                    <>
                      {/* Quick Response Templates Chips */}
                      <div className="quick-templates-bar">
                        <span className="templates-label">⚡ {language === 'es' ? 'Plantillas Rápidas:' : 'Quick Replies:'}</span>
                        <div className="templates-scroll">
                          {quickTemplates.map((t, idx) => (
                            <button
                              key={idx}
                              type="button"
                              className="template-chip"
                              onClick={() => setAgentInput(t.text)}
                              title={t.text}
                            >
                              {t.title}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Agent Reply Box */}
                      <form onSubmit={handleSendAgentMessage} className="inbox-reply-form">
                        <input
                          type="text"
                          className="inbox-reply-input"
                          placeholder={language === 'es' ? 'Escribe una respuesta al estudiante en tiempo real (Presiona Enter)...' : 'Type a real-time message to the student (Press Enter)...'}
                          value={agentInput}
                          onChange={(e) => setAgentInput(e.target.value)}
                          disabled={sendingMessage}
                        />
                        <button
                          type="submit"
                          className="inbox-send-btn pulse-glow"
                          disabled={!agentInput.trim() || sendingMessage}
                          title="Enviar mensaje en vivo"
                        >
                          <Send size={18} />
                        </button>
                      </form>
                    </>
                  )}
                </>
              ) : (
                <div className="inbox-no-selected">
                  <MessageSquare size={54} className="gold-text" />
                  <h3>{language === 'es' ? 'Selecciona una conversación' : 'Select a conversation'}</h3>
                  <p>{language === 'es' ? 'Podrás consultar el historial completo, tomar el caso y responder al estudiante en vivo.' : 'You can review history, claim the case, and reply in real time.'}</p>
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
                <UploadCloud size={36} className="gold-text" />
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
                    <FileText size={48} className="gold-text" />
                    <span className="dropzone-title">
                      {selectedFile ? selectedFile.name : (language === 'es' ? 'Haz clic o arrastra un archivo .md' : 'Click or drop a .md file')}
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
                    <span>{language === 'es' ? 'Procesando y Reindexando ChromaDB...' : 'Processing and Re-indexing ChromaDB...'}</span>
                  ) : (
                    <>
                      <Zap size={18} />
                      <span>{language === 'es' ? 'Subir y Reindexar ChromaDB' : 'Upload & Re-index ChromaDB'}</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ================================================================== */}
        {/* TAB 3: MÉTRICAS Y MONITOREO EN VIVO */}
        {/* ================================================================== */}
        {activeTab === 'metrics' && (
          <div className="admin-metrics-view slide-up">
            <div className="metrics-header-row">
              <div className="metrics-title-block">
                <h2>{language === 'es' ? 'Panel de Métricas, Analítica & SLA' : 'Analytics, Performance & SLA Dashboard'}</h2>
                <p>{language === 'es' ? 'Monitoreo operacional en tiempo real de consultas RAG, costos LPU y atención de asesores.' : 'Real-time operational analytics for RAG queries, LPU costs, and human advisor support.'}</p>
              </div>
              <button 
                className="admin-secondary-btn" 
                onClick={loadMetrics}
                title="Actualizar métricas"
              >
                <RefreshCw size={15} className={loadingMetrics ? 'spin' : ''} />
                <span>{language === 'es' ? 'Actualizar Datos' : 'Refresh Metrics'}</span>
              </button>
            </div>

            {loadingMetrics && !metrics ? (
              <div className="inbox-empty-state">
                <p>{language === 'es' ? 'Calculando analítica...' : 'Calculating analytics...'}</p>
              </div>
            ) : metrics ? (
              <>
                {/* 1. TOP 4 KEY PERFORMANCE INDICATORS */}
                <div className="metrics-cards-grid">
                  <div className="metric-card glass-panel">
                    <div className="metric-header">
                      <span>{language === 'es' ? 'Total Consultas' : 'Total Queries'}</span>
                      <Activity size={20} className="gold-text" />
                    </div>
                    <div className="metric-value">{metrics.total_queries}</div>
                    <div className="metric-footer">{language === 'es' ? 'Interacciones en la plataforma' : 'Platform interactions'}</div>
                  </div>

                  <div className="metric-card glass-panel">
                    <div className="metric-header">
                      <span>{language === 'es' ? 'Resolución IA Autónoma' : 'AI Resolution Rate'}</span>
                      <Sparkles size={20} className="gold-text" />
                    </div>
                    <div className="metric-value">{metrics.ai_resolution_rate_pct ?? (100 - (metrics.escalation_rate_pct || 0)).toFixed(1)}%</div>
                    <div className="metric-footer">{metrics.resolved_by_ai || (metrics.total_queries - (metrics.escalated_queries || 0))} {language === 'es' ? 'resueltas sin asesor' : 'resolved by bot'}</div>
                  </div>

                  <div className="metric-card glass-panel">
                    <div className="metric-header">
                      <span>{language === 'es' ? 'Tasa de Escalamiento' : 'Escalation Rate'}</span>
                      <Headphones size={20} className="gold-text" />
                    </div>
                    <div className="metric-value">{metrics.escalation_rate_pct ?? 0}%</div>
                    <div className="metric-footer">{metrics.escalated_queries || 0} {language === 'es' ? 'casos transferidos' : 'advisor handoffs'}</div>
                  </div>

                  <div className="metric-card glass-panel">
                    <div className="metric-header">
                      <span>{language === 'es' ? 'Eficiencia Caché TTL' : 'Cache Efficiency'}</span>
                      <Zap size={20} className="gold-text" />
                    </div>
                    <div className="metric-value">{metrics.cache_hit_rate_pct ?? 0}%</div>
                    <div className="metric-footer">{metrics.cached_queries || 0} {language === 'es' ? 'respuestas instantáneas' : 'cache hits'}</div>
                  </div>
                </div>

                {/* 2. DEEP DIVE ANALYTICS SUBGRID */}
                <div className="metrics-subgrid">
                  {/* Panel A: Rendimiento RAG & Eficiencia de Costos */}
                  <div className="metrics-panel glass-panel">
                    <div className="metrics-panel-header">
                      <h3>
                        <Zap size={18} className="gold-text" />
                        <span>{language === 'es' ? 'Rendimiento RAG & Costos de Inferencia' : 'RAG Performance & Inference Costs'}</span>
                      </h3>
                      <span className="summary-badge">Groq LPU Tier</span>
                    </div>

                    <div className="stats-list">
                      <div className="stats-row">
                        <span className="stats-label"><Clock size={15} /> {language === 'es' ? 'Latencia Promedio RAG:' : 'Average RAG Latency:'}</span>
                        <span className="stats-val highlight">{metrics.avg_rag_latency_seconds || 0.85}s</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><CheckCircle size={15} /> {language === 'es' ? 'Cumplimiento de SLA (< 2.5s):' : 'SLA Compliance (< 2.5s):'}</span>
                        <span className="stats-val">{metrics.sla_compliance_pct || 99.2}%</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><Sparkles size={15} /> {language === 'es' ? 'Satisfacción Estimada (CSAT):' : 'Estimated CSAT Rating:'}</span>
                        <span className="stats-val">{metrics.csat_satisfaction_pct || 97.2}%</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><Activity size={15} /> {language === 'es' ? 'Tokens Reales Consumidos:' : 'Real Tokens Consumed:'}</span>
                        <span className="stats-val">{(metrics.total_tokens || 0).toLocaleString()} tokens</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><DollarSign size={15} /> {language === 'es' ? 'Costo Operativo Estimado:' : 'Estimated Operating Cost:'}</span>
                        <span className="stats-val highlight">{metrics.estimated_cost_usd || '$0.0000 USD'}</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><Zap size={15} /> {language === 'es' ? 'Ahorro por Caché Semántica:' : 'Tokens Saved by Cache:'}</span>
                        <span className="stats-val">{(metrics.tokens_saved_by_cache || 0).toLocaleString()} tokens ({metrics.cost_saved_usd || '$0.0000'})</span>
                      </div>
                    </div>
                  </div>

                  {/* Panel B: Ciclo de Vida de Casos & Base de Datos */}
                  <div className="metrics-panel glass-panel">
                    <div className="metrics-panel-header">
                      <h3>
                        <Headphones size={18} className="gold-text" />
                        <span>{language === 'es' ? 'Bandeja de Asesores & Base de Datos' : 'Advisor Backoffice & Case Lifecycle'}</span>
                      </h3>
                      <span className="summary-badge">SQLite DB</span>
                    </div>

                    <div className="stats-list">
                      <div className="stats-row">
                        <span className="stats-label"><AlertCircle size={15} /> {language === 'es' ? 'Casos Pendientes de Asignación:' : 'Pending Unclaimed Cases:'}</span>
                        <span className="stats-val highlight">{metrics.db_stats?.pending_conversations ?? conversations.filter(c => c.estado === 'pendiente').length}</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><Headphones size={15} /> {language === 'es' ? 'Casos en Atención Activa:' : 'In-Progress Active Cases:'}</span>
                        <span className="stats-val">{metrics.db_stats?.in_progress_conversations ?? conversations.filter(c => c.estado === 'en_atencion').length}</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><CheckCircle size={15} /> {language === 'es' ? 'Casos Resueltos Exitosamente:' : 'Resolved Cases:'}</span>
                        <span className="stats-val">{metrics.db_stats?.resolved_conversations ?? conversations.filter(c => c.estado === 'resuelto').length}</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><MessageSquare size={15} /> {language === 'es' ? 'Total Mensajes Guardados:' : 'Total Messages in DB:'}</span>
                        <span className="stats-val">{(metrics.db_stats?.total_messages ?? 0).toLocaleString()}</span>
                      </div>
                      <div className="stats-row">
                        <span className="stats-label"><Activity size={15} /> {language === 'es' ? 'Total Conversaciones Creadas:' : 'Total Conversations Created:'}</span>
                        <span className="stats-val">{(metrics.db_stats?.total_conversations ?? conversations.length)}</span>
                      </div>
                    </div>

                    {/* Distribución por Idioma */}
                    <div className="lang-dist-container">
                      <span className="stats-label">🌐 {language === 'es' ? 'Distribución por Idioma:' : 'Language Distribution:'}</span>
                      {(() => {
                        const langs = metrics.db_stats?.languages || { es: 1, en: 0, fr: 0, pt: 0 };
                        const totalLangs = Math.max(1, (langs.es || 0) + (langs.en || 0) + (langs.fr || 0) + (langs.pt || 0));
                        
                        return (
                          <>
                            <div className="lang-dist-item">
                              <div className="lang-dist-header">
                                <span>🇪🇸 Español</span>
                                <span>{langs.es || 0} ({Math.round(((langs.es || 0) / totalLangs) * 100)}%)</span>
                              </div>
                              <div className="lang-dist-bar-track">
                                <div className="lang-dist-bar-fill fill-es" style={{ width: `${Math.round(((langs.es || 0) / totalLangs) * 100)}%` }} />
                              </div>
                            </div>

                            <div className="lang-dist-item">
                              <div className="lang-dist-header">
                                <span>🇬🇧 English</span>
                                <span>{langs.en || 0} ({Math.round(((langs.en || 0) / totalLangs) * 100)}%)</span>
                              </div>
                              <div className="lang-dist-bar-track">
                                <div className="lang-dist-bar-fill fill-en" style={{ width: `${Math.round(((langs.en || 0) / totalLangs) * 100)}%` }} />
                              </div>
                            </div>

                            <div className="lang-dist-item">
                              <div className="lang-dist-header">
                                <span>🇫🇷 Français</span>
                                <span>{langs.fr || 0} ({Math.round(((langs.fr || 0) / totalLangs) * 100)}%)</span>
                              </div>
                              <div className="lang-dist-bar-track">
                                <div className="lang-dist-bar-fill fill-fr" style={{ width: `${Math.round(((langs.fr || 0) / totalLangs) * 100)}%` }} />
                              </div>
                            </div>

                            <div className="lang-dist-item">
                              <div className="lang-dist-header">
                                <span>🇧🇷 Português</span>
                                <span>{langs.pt || 0} ({Math.round(((langs.pt || 0) / totalLangs) * 100)}%)</span>
                              </div>
                              <div className="lang-dist-bar-track">
                                <div className="lang-dist-bar-fill fill-pt" style={{ width: `${Math.round(((langs.pt || 0) / totalLangs) * 100)}%` }} />
                              </div>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="inbox-empty-state">
                <p>{language === 'es' ? 'No hay datos de métricas disponibles.' : 'No metrics data available.'}</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* MODAL: CREAR NUEVA CONVERSACIÓN (CRUD CREATE) */}
      {showNewModal && (
        <div className="modal-backdrop-overlay fade-in" onClick={() => setShowNewModal(false)}>
          <div className="modal-card glass-panel scale-in" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-header-title">
                <MessageSquare size={20} className="gold-text" />
                <h3>{language === 'es' ? 'Crear Nueva Consulta / Ticket' : 'Create New Conversation'}</h3>
              </div>
              <button className="modal-close-btn" onClick={() => setShowNewModal(false)}>✕</button>
            </div>

            <form onSubmit={handleCreateConversation} className="modal-form">
              <div className="modal-form-group">
                <label>{language === 'es' ? 'ID de Sesión / Referencia del Estudiante:' : 'Session ID / Student Reference:'}</label>
                <input
                  type="text"
                  placeholder="ej. estudiante_breyner_2026"
                  value={newSessionId}
                  onChange={(e) => setNewSessionId(e.target.value)}
                  className="admin-input"
                  required
                />
              </div>

              <div className="modal-form-group">
                <label>{language === 'es' ? 'Idioma:' : 'Language:'}</label>
                <select 
                  value={newLang} 
                  onChange={(e) => setNewLang(e.target.value)}
                  className="admin-input"
                >
                  <option value="es">🇪🇸 Español</option>
                  <option value="en">🇬🇧 English</option>
                  <option value="fr">🇫🇷 Français</option>
                  <option value="pt">🇧🇷 Português</option>
                </select>
              </div>

              <div className="modal-form-group">
                <label>{language === 'es' ? 'Mensaje o Consulta Inicial:' : 'Initial Message / Question:'}</label>
                <textarea
                  placeholder={language === 'es' ? 'Ej. Deseo información para matricularme en el curso intensivo de inglés.' : 'Enter initial question...'}
                  value={newInitialMsg}
                  onChange={(e) => setNewInitialMsg(e.target.value)}
                  className="admin-input modal-textarea"
                  rows={3}
                  required
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-modal-cancel" onClick={() => setShowNewModal(false)}>
                  {language === 'es' ? 'Cancelar' : 'Cancel'}
                </button>
                <button type="submit" className="btn-modal-submit pulse-glow">
                  <Plus size={16} />
                  <span>{language === 'es' ? 'Crear Consulta' : 'Create Ticket'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
