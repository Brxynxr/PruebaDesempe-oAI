import React, { useState, useEffect, useRef } from 'react';
import {
  Inbox,
  FileText,
  BarChart3,
  LogOut,
  Send,
  User,
  CheckCircle2,
  Trash2,
  Upload,
  RefreshCw,
  Volume2,
  VolumeX,
  Clock,
  Sparkles,
  Phone,
  BookOpen,
  Check,
  Search,
  MessageSquare,
  Shield,
  Loader2,
  CheckSquare,
  Square,
  MinusSquare
} from 'lucide-react';
import {
  getAdminProfile,
  getAdminToken,
  removeAdminToken,
  getAdminUsername,
  getAdminRole,
  getAdminFullName,
  getAllConversations,
  getPendingConversations,
  getConversationDetail,
  claimConversation,
  resolveConversation,
  sendAgentMessage,
  deleteConversation,
  bulkDeleteConversations,
  getDocuments,
  uploadDocument,
  deleteDocument,
  getMetrics,
  WS_BASE_URL
} from '../services/api';

function renderInlineFormatting(text) {
  if (!text) return null;
  const parts = [];
  let lastIndex = 0;
  const regex = /\*\*(.*?)\*\*|\*(.*?)\*/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const boldText = match[1] || match[2];
    parts.push(
      <strong key={match.index} className="font-semibold text-ink">
        {boldText}
      </strong>
    );
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

function FormattedAdvisorMessage({ text, isAgent = false }) {
  if (!text) return null;

  // Handle lead registration info specially (Discrete clean card without showing raw technical history)
  if (text.startsWith('[Lead Registrado]')) {
    const raw = text.replace('[Lead Registrado]', '').trim();
    const nameMatch = raw.match(/Nombre:\s*([^,]+)/i);
    const phoneMatch = raw.match(/Tel:\s*([^,]+)/i);
    const progMatch = raw.match(/Programa:\s*([^,]+)/i);

    const name = nameMatch ? nameMatch[1].trim() : 'Estudiante';
    const prog = progMatch ? progMatch[1].trim() : 'General';
    const phone = phoneMatch ? phoneMatch[1].trim() : '';

    return (
      <div className="rounded-2xl bg-amber-50 border border-amber-200/80 p-3.5 text-xs text-ink space-y-2 shadow-xs">
        <div className="font-bold text-amber-950 flex items-center gap-1.5 pb-1.5 border-b border-amber-200/60">
          <Phone size={13} className="text-amber-800" />
          <span>Solicitud de Asesoría Recibida</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          <div>
            <span className="text-ink/60 block">Estudiante:</span>
            <span className="font-semibold text-ink">{name}</span>
          </div>
          <div>
            <span className="text-ink/60 block">Programa de Interés:</span>
            <span className="font-semibold text-brand">{prog}</span>
          </div>
        </div>
        {phone && (
          <div className="pt-1 text-[11px] text-ink/70">
            <span className="text-ink/60">Contacto registrado: </span>
            <span className="font-mono font-medium">+{phone.replace(/^\+/, '')}</span>
          </div>
        )}
      </div>
    );
  }

  // Pre-process text: normalize <br>, remove raw html artifacts
  const cleanText = text
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/?[bi]>/gi, '')
    .replace(/&nbsp;/gi, ' ');

  const lines = cleanText.split('\n');
  const elements = [];
  let currentList = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="my-1.5 space-y-1.5 pl-1.5">
          {currentList.map((item, idx) => (
            <li key={idx} className={`flex items-start gap-2 text-xs leading-relaxed ${isAgent ? 'text-cream/90' : 'text-ink/90'}`}>
              <span className={`mt-1.5 size-1.5 shrink-0 rounded-full ${isAgent ? 'bg-gold' : 'bg-brand/70'}`} />
              <div className="flex-1">{renderInlineFormatting(item)}</div>
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }

    // 1. Check if line is a Section / Category Header (e.g. **Modalidades:** or - **Modalidades:** or Modalidades:)
    const boldHeaderMatch = trimmed.match(/^[-*•]?\s*\*\*([^*:\n]+):?\*\*:?$/);
    const mdHeaderMatch = trimmed.match(/^(?:###|##|#)\s+(.+)$/);
    const isColonTitle = !boldHeaderMatch && !mdHeaderMatch && /^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúÁÉÍÓÚñÑ\s()/-]{2,45}:$/.test(trimmed) && !trimmed.includes('http');

    if (boldHeaderMatch || mdHeaderMatch || isColonTitle) {
      flushList();
      const headerTitle = boldHeaderMatch ? boldHeaderMatch[1] : mdHeaderMatch ? mdHeaderMatch[1] : trimmed.replace(/:$/, '');
      elements.push(
        <div key={`section-hdr-${index}`} className={`mt-2.5 mb-1 flex items-center gap-1.5 border-b pb-0.5 ${isAgent ? 'border-white/15 text-gold' : 'border-black/10 text-ink'}`}>
          <span className={`size-1.5 rounded-sm shrink-0 ${isAgent ? 'bg-gold' : 'bg-brand'}`} />
          <span className="text-[11px] font-bold uppercase tracking-wider">
            {headerTitle}
          </span>
        </div>
      );
      return;
    }

    // 2. Check for blockquote (> **Nota:** or > **Importante:**)
    if (trimmed.startsWith('>')) {
      flushList();
      const quoteText = trimmed.replace(/^>\s*/, '');
      elements.push(
        <div key={`quote-${index}`} className={`my-2 rounded-xl p-2.5 text-xs leading-relaxed ${isAgent ? 'bg-white/10 border-l-2 border-gold text-cream' : 'bg-gold/15 border-l-2 border-brand text-ink'}`}>
          {renderInlineFormatting(quoteText)}
        </div>
      );
      return;
    }

    // 3. Check for bullet lists (-, *, •, or numbered 1., 2.)
    if (/^[-*•]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
      const content = trimmed.replace(/^[-*•]\s+/, '').replace(/^\d+\.\s+/, '');
      currentList.push(content);
      return;
    } else {
      flushList();
    }

    // Regular paragraph
    elements.push(
      <p key={`p-${index}`} className={`my-1 text-xs leading-relaxed ${isAgent ? 'text-cream/95' : 'text-ink/90'}`}>
        {renderInlineFormatting(trimmed)}
      </p>
    );
  });

  flushList();

  return <div className="space-y-1">{elements}</div>;
}

export default function AdminDashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('inbox'); // 'inbox' | 'documents' | 'metrics'
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [selectedDetails, setSelectedDetails] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'pendiente' | 'en_atencion' | 'resuelto'
  const [searchTerm, setSearchTerm] = useState('');
  const [messageInput, setMessageInput] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  
  // Document CRUD State
  const [documents, setDocuments] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [deletingDoc, setDeletingDoc] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Custom Confirmation Modal & Toast State
  const [confirmModal, setConfirmModal] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast((prev) => (prev?.message === message ? null : prev));
    }, 4000);
  };

  // Audio Notifications State
  const [audioEnabled, setAudioEnabled] = useState(true);
  const audioContextRef = useRef(null);

  // Profile & Connection State
  const [profile, setProfile] = useState({
    username: getAdminUsername(),
    role: getAdminRole(),
    fullName: getAdminFullName()
  });
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);

  // Play gentle alert chime for new pending escalations
  const playAlertSound = () => {
    if (!audioEnabled) return;
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }
      const ctx = audioContextRef.current;
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15); // A5
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch (e) {
      console.warn('Audio alert error:', e);
    }
  };

  // Fetch conversations
  const loadConversations = async () => {
    try {
      setLoading(true);
      const data = await getAllConversations(statusFilter === 'all' ? null : statusFilter);
      setConversations(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch metrics
  const loadMetrics = async (showNotification = false) => {
    try {
      setMetricsLoading(true);
      const data = await getMetrics();
      setMetrics(data);
      if (showNotification) {
        showToast('Métricas actualizadas exitosamente.');
      }
    } catch (err) {
      console.error('Error loading metrics:', err);
      if (showNotification) {
        showToast(err.message || 'Error al actualizar métricas', 'error');
      }
    } finally {
      setMetricsLoading(false);
    }
  };

  // Fetch documents for RAG base
  const loadDocList = async () => {
    try {
      setDocsLoading(true);
      const docs = await getDocuments();
      setDocuments(Array.isArray(docs) ? docs : []);
    } catch (err) {
      console.error('Error loading documents:', err);
    } finally {
      setDocsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadConversations();
    loadMetrics();
    loadDocList();

    getAdminProfile()
      .then((p) => {
        setProfile({
          username: p.username,
          role: p.role,
          fullName: p.full_name || p.username
        });
      })
      .catch(() => {
        // use local cache
      });
  }, [statusFilter]);

  // Load documents when tab switches to documents
  useEffect(() => {
    if (activeTab === 'documents') {
      loadDocList();
    }
  }, [activeTab]);

  // Load conversation details when selected
  useEffect(() => {
    if (selectedConversation?.id) {
      getConversationDetail(selectedConversation.id)
        .then((data) => setSelectedDetails(data))
        .catch((err) => console.error('Error loading conversation details:', err));
    } else {
      setSelectedDetails(null);
    }
  }, [selectedConversation]);

  // Auto scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [selectedDetails?.messages]);

  const selectedConversationRef = useRef(selectedConversation);
  useEffect(() => {
    selectedConversationRef.current = selectedConversation;
  }, [selectedConversation]);

  // WebSocket for real-time backoffice updates
  useEffect(() => {
    const token = getAdminToken();
    if (!token) return;

    let isMounted = true;
    let reconnectTimeout = null;

    const connectWs = () => {
      const wsUrl = `${WS_BASE_URL}/agent?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isMounted) setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'new_conversation' || data.type === 'status_update' || data.type === 'conversation_claimed') {
            loadConversations();
            loadMetrics();
            if (data.status === 'pendiente') {
              playAlertSound();
            }
          }

          if (data.type === 'new_message' || data.type === 'user_message' || data.type === 'agent_message') {
            const currentSelected = selectedConversationRef.current;
            if (currentSelected && (data.conversation_id === currentSelected.id || data.session_id === currentSelected.session_id)) {
              getConversationDetail(currentSelected.id).then(setSelectedDetails);
            }
            loadConversations();
          }
        } catch (err) {
          console.error('WS parse error:', err);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          setIsConnected(false);
          // Try reconnecting after 3 seconds
          reconnectTimeout = setTimeout(() => {
            if (isMounted) connectWs();
          }, 3000);
        }
      };

      ws.onerror = (err) => {
        console.warn('WS error:', err);
      };
    };

    connectWs();

    return () => {
      isMounted = false;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, [audioEnabled]);

  const handleClaim = async (id) => {
    try {
      await claimConversation(id);
      await loadConversations();
      const updated = await getConversationDetail(id);
      setSelectedDetails(updated);
      setSelectedConversation((prev) => (prev?.id === id ? { ...prev, estado: 'en_atencion' } : prev));
    } catch (err) {
      setErrorMsg(err.message || 'Error al reclamar caso');
    }
  };

  const handleResolve = async (id) => {
    try {
      await resolveConversation(id);
      await loadConversations();
      const updated = await getConversationDetail(id);
      setSelectedDetails(updated);
      setSelectedConversation((prev) => (prev?.id === id ? { ...prev, estado: 'resuelto' } : prev));
    } catch (err) {
      setErrorMsg(err.message || 'Error al resolver caso');
    }
  };

  const handleDelete = (id) => {
    setConfirmModal({
      title: '¿Eliminar conversación?',
      message: 'Se eliminará el registro y todo el historial de mensajes de esta conversación. Esta acción no se puede deshacer.',
      confirmText: 'Sí, eliminar',
      onConfirm: async () => {
        try {
          await deleteConversation(id);
          if (selectedConversation?.id === id) {
            setSelectedConversation(null);
            setSelectedDetails(null);
          }
          await loadConversations();
          showToast('Conversación eliminada exitosamente.');
        } catch (err) {
          showToast(err.message || 'Error al eliminar conversación', 'error');
        }
      }
    });
  };

  const handleToggleSelect = (id, e) => {
    e.stopPropagation();
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    const visibleIds = filteredConversations.map((c) => c.id);
    const allSelected = visibleIds.length > 0 && visibleIds.every((id) => selectedIds.includes(id));
    if (allSelected) {
      setSelectedIds((prev) => prev.filter((id) => !visibleIds.includes(id)));
    } else {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...visibleIds])));
    }
  };

  const handleBulkDelete = () => {
    if (selectedIds.length === 0) return;
    const count = selectedIds.length;
    setConfirmModal({
      title: `¿Eliminar ${count} ${count === 1 ? 'conversación' : 'conversaciones'}?`,
      message: `Se eliminarán permanentemente las ${count} conversaciones seleccionadas y todo su historial. Esta acción no se puede deshacer.`,
      confirmText: `Sí, eliminar (${count})`,
      onConfirm: async () => {
        try {
          await bulkDeleteConversations(selectedIds);
          if (selectedConversation && selectedIds.includes(selectedConversation.id)) {
            setSelectedConversation(null);
            setSelectedDetails(null);
          }
          setSelectedIds([]);
          await loadConversations();
          showToast(`${count} ${count === 1 ? 'conversación eliminada' : 'conversaciones eliminadas'} exitosamente.`);
        } catch (err) {
          showToast(err.message || 'Error al eliminar conversaciones', 'error');
        }
      }
    });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!selectedConversation?.id || !messageInput.trim()) return;

    const text = messageInput.trim();
    setMessageInput('');

    try {
      await sendAgentMessage(selectedConversation.id, text);
      const updated = await getConversationDetail(selectedConversation.id);
      setSelectedDetails(updated);
      await loadConversations();
    } catch (err) {
      showToast(err.message || 'Error enviando mensaje', 'error');
    }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploadLoading(true);
    setUploadSuccess(null);
    setUploadError(null);

    try {
      const res = await uploadDocument(uploadFile);
      setUploadSuccess(`Documento "${uploadFile.name}" procesado e indexado exitosamente en ChromaDB (${res.total_chunks || 'RAG'} fragmentos totales).`);
      setUploadFile(null);
      await loadDocList();
      showToast(`Documento "${uploadFile.name}" indexado exitosamente.`);
    } catch (err) {
      setUploadError(err.message || 'Error al indexar documento');
      showToast(err.message || 'Error al indexar documento', 'error');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDeleteDoc = (filename) => {
    setConfirmModal({
      title: '¿Eliminar documento de la Base RAG?',
      message: `Se eliminará permanentemente el archivo "${filename}" y se purgarán todos sus fragmentos de búsqueda vectorial en ChromaDB.`,
      confirmText: 'Sí, eliminar documento',
      onConfirm: async () => {
        try {
          setDeletingDoc(filename);
          setUploadSuccess(null);
          setUploadError(null);
          const res = await deleteDocument(filename);
          setUploadSuccess(res.message || `Documento "${filename}" eliminado correctamente.`);
          await loadDocList();
          showToast(`Documento "${filename}" eliminado de ChromaDB.`);
        } catch (err) {
          setUploadError(err.message || 'Error al eliminar documento');
          showToast(err.message || 'Error al eliminar documento', 'error');
        } finally {
          setDeletingDoc(null);
        }
      }
    });
  };

  const filteredConversations = conversations.filter((c) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      c.session_id?.toLowerCase().includes(term) ||
      c.idioma?.toLowerCase().includes(term) ||
      c.estado?.toLowerCase().includes(term) ||
      (c.messages && c.messages.some((m) => m.contenido?.toLowerCase().includes(term)))
    );
  });

  return (
    <div className="relative min-h-screen w-full bg-cream font-sans text-ink antialiased selection:bg-brand/30">
      {/* Warm gradient background */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(135deg, #FFF6EC 0%, #FCE3D2 38%, #F7D2CB 66%, #EAD7E8 100%)",
          }}
        />
        <div className="absolute -top-40 -right-28 h-[560px] w-[560px] rounded-full bg-gold/40 blur-3xl" />
        <div className="absolute -bottom-52 -left-40 h-[520px] w-[520px] rounded-full bg-accent-rose/25 blur-3xl" />
      </div>

      {/* Top Navbar */}
      <header className="border-b border-black/5 bg-white/40 backdrop-blur-md sticky top-0 z-30">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="grid size-9 place-items-center rounded-2xl bg-white/70 ring-1 ring-black/5 text-brand font-bold font-display">
                L
              </div>
              <div>
                <span className="text-sm font-semibold tracking-tight font-display text-ink block">
                  Academia Lumina
                </span>
                <span className="text-[11px] text-ink/60 font-medium">Portal del Asesor</span>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center gap-1.5 bg-white/40 p-1 rounded-2xl ring-1 ring-black/5">
              <button
                onClick={() => setActiveTab('inbox')}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-medium transition ${
                  activeTab === 'inbox'
                    ? 'bg-ink text-cream shadow-xs'
                    : 'text-ink/70 hover:text-ink hover:bg-white/50'
                }`}
              >
                <Inbox size={14} />
                <span>Bandeja de Chats</span>
                {conversations.filter((c) => c.estado === 'pendiente').length > 0 && (
                  <span className="rounded-full bg-amber-400 px-1.5 py-0.2 text-[10px] font-bold text-ink">
                    {conversations.filter((c) => c.estado === 'pendiente').length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('documents')}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-medium transition ${
                  activeTab === 'documents'
                    ? 'bg-ink text-cream shadow-xs'
                    : 'text-ink/70 hover:text-ink hover:bg-white/50'
                }`}
              >
                <FileText size={14} />
                <span>Base RAG</span>
              </button>
              <button
                onClick={() => {
                  setActiveTab('metrics');
                  loadMetrics();
                }}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-medium transition ${
                  activeTab === 'metrics'
                    ? 'bg-ink text-cream shadow-xs'
                    : 'text-ink/70 hover:text-ink hover:bg-white/50'
                }`}
              >
                <BarChart3 size={14} />
                <span>Métricas y SLA</span>
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            {/* Live Connection & Audio toggle */}
            <div className="hidden sm:flex items-center gap-2 rounded-full bg-white/50 px-3 py-1 text-[11px] ring-1 ring-black/5">
              <span className={`size-2 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-rose-400 animate-pulse'}`} />
              <span className="text-ink/70">{isConnected ? 'En vivo' : 'Reconectando'}</span>
            </div>

            <button
              onClick={() => setAudioEnabled(!audioEnabled)}
              className="grid size-9 place-items-center rounded-2xl bg-white/50 ring-1 ring-black/5 text-ink/70 transition hover:bg-white/80"
              title={audioEnabled ? 'Alertas sonoras activas' : 'Alertas silenciadas'}
            >
              {audioEnabled ? <Volume2 size={16} /> : <VolumeX size={16} className="text-ink/40" />}
            </button>

            <div className="flex items-center gap-2.5 border-l border-black/5 pl-3">
              <div className="grid size-8 place-items-center rounded-full bg-gold/50 text-xs font-bold text-ink font-display">
                {profile.fullName.charAt(0).toUpperCase()}
              </div>
              <div className="hidden lg:block text-left text-xs">
                <div className="font-semibold text-ink leading-tight">{profile.fullName}</div>
                <div className="text-[10px] text-ink/60 uppercase tracking-wider">{profile.role}</div>
              </div>
              <button
                onClick={onLogout}
                className="grid size-8 place-items-center rounded-2xl text-ink/60 transition hover:bg-rose/40 hover:text-ink"
                title="Cerrar sesión"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto max-w-7xl px-6 py-6">
        {/* INBOX TAB */}
        {activeTab === 'inbox' && (
          <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)] min-h-[550px]">
            {/* Left Column: Conversation Queue */}
            <div className="col-span-12 md:col-span-4 lg:col-span-4 flex flex-col rounded-3xl bg-white/50 ring-1 ring-black/5 backdrop-blur-md overflow-hidden shadow-sm">
              {/* Filter pills & search */}
              <div className="p-4 border-b border-black/5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-ink/60 uppercase tracking-wider">
                      Conversaciones ({filteredConversations.length})
                    </span>
                    {filteredConversations.length > 0 && (
                      <button
                        onClick={handleSelectAll}
                        className="flex items-center gap-1 rounded-lg px-2 py-0.5 text-[11px] font-medium text-ink/70 hover:bg-black/5 hover:text-ink transition"
                        title={
                          filteredConversations.length > 0 && filteredConversations.every((c) => selectedIds.includes(c.id))
                            ? 'Deseleccionar todas'
                            : 'Seleccionar todas'
                        }
                      >
                        {filteredConversations.length > 0 && filteredConversations.every((c) => selectedIds.includes(c.id)) ? (
                          <CheckSquare size={13} className="text-brand" />
                        ) : selectedIds.length > 0 && filteredConversations.some((c) => selectedIds.includes(c.id)) ? (
                          <MinusSquare size={13} className="text-brand" />
                        ) : (
                          <Square size={13} className="text-ink/40" />
                        )}
                        <span>
                          {filteredConversations.length > 0 && filteredConversations.every((c) => selectedIds.includes(c.id))
                            ? 'Deseleccionar'
                            : 'Todas'}
                        </span>
                      </button>
                    )}
                  </div>
                  <button
                    onClick={loadConversations}
                    className="grid size-7 place-items-center rounded-xl text-ink/60 hover:bg-white/80"
                    title="Refrescar lista"
                  >
                    <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                  </button>
                </div>

                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Buscar estudiante o mensaje..."
                    className="w-full rounded-2xl bg-white/80 pl-9 pr-3 py-2 text-xs text-ink outline-none ring-1 ring-black/10 focus:ring-2 focus:ring-ink"
                  />
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {[
                    { id: 'all', label: 'Todas' },
                    { id: 'pendiente', label: 'Pendientes' },
                    { id: 'en_atencion', label: 'En curso' },
                    { id: 'resuelto', label: 'Resueltas' }
                  ].map((filter) => (
                    <button
                      key={filter.id}
                      onClick={() => setStatusFilter(filter.id)}
                      className={`rounded-full px-3 py-1 text-[11px] font-medium transition ${
                        statusFilter === filter.id
                          ? 'bg-ink text-cream'
                          : 'bg-white/60 text-ink/70 hover:bg-white'
                      }`}
                    >
                      {filter.label}
                    </button>
                  ))}
                </div>

                {/* Bulk Action Bar when items are selected */}
                {selectedIds.length > 0 && (
                  <div className="flex items-center justify-between gap-2 rounded-2xl bg-ink p-2.5 text-cream shadow-md animate-rise">
                    <div className="flex items-center gap-2 pl-1.5">
                      <span className="grid size-5 place-items-center rounded-full bg-gold text-[10px] font-bold text-ink">
                        {selectedIds.length}
                      </span>
                      <span className="text-xs font-medium">
                        {selectedIds.length === 1 ? '1 seleccionada' : `${selectedIds.length} seleccionadas`}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => setSelectedIds([])}
                        className="rounded-xl px-2.5 py-1 text-[11px] text-cream/70 hover:bg-white/10 hover:text-cream transition"
                      >
                        Cancelar
                      </button>
                      <button
                        onClick={handleBulkDelete}
                        className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-rose-500 transition cursor-pointer"
                      >
                        <Trash2 size={13} />
                        <span>Eliminar ({selectedIds.length})</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Conversation List */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {filteredConversations.length === 0 ? (
                  <div className="py-12 text-center text-xs text-ink/50">
                    No hay conversaciones en esta categoría.
                  </div>
                ) : (
                  filteredConversations.map((conv) => {
                    const isSelected = selectedConversation?.id === conv.id;
                    const isChecked = selectedIds.includes(conv.id);
                    const lastMsg = conv.messages && conv.messages.length > 0 ? conv.messages[conv.messages.length - 1] : null;

                    return (
                      <div
                        key={conv.id}
                        onClick={() => setSelectedConversation(conv)}
                        className={`group cursor-pointer rounded-2xl p-3.5 transition duration-200 ring-1 flex items-start gap-3 ${
                          isChecked
                            ? 'bg-brand/[0.06] ring-2 ring-brand/80 shadow-xs'
                            : isSelected
                              ? 'bg-white shadow-md ring-brand'
                              : 'bg-white/40 ring-black/5 hover:bg-white/80'
                        }`}
                      >
                        {/* Custom Checkbox */}
                        <div
                          onClick={(e) => handleToggleSelect(conv.id, e)}
                          className={`mt-0.5 grid size-5 shrink-0 place-items-center rounded-lg border transition cursor-pointer ${
                            isChecked
                              ? 'border-brand bg-brand text-cream shadow-2xs'
                              : 'border-black/20 bg-white/90 hover:border-brand/70 group-hover:border-black/40'
                          }`}
                          title={isChecked ? 'Deseleccionar' : 'Seleccionar'}
                        >
                          {isChecked && <Check size={12} className="stroke-[3]" />}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2 min-w-0">
                              <span className="text-xs font-bold text-ink truncate max-w-[120px]">
                                {conv.session_id}
                              </span>
                              <span className="rounded-full bg-black/5 px-2 py-0.5 text-[10px] uppercase font-semibold text-ink/60 shrink-0">
                                {conv.idioma || 'es'}
                              </span>
                            </div>

                            <span
                              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold shrink-0 ${
                                conv.estado === 'pendiente'
                                  ? 'bg-amber-100 text-amber-900 animate-pulse'
                                  : conv.estado === 'en_atencion'
                                    ? 'bg-gold/40 text-ink font-bold'
                                    : conv.estado === 'resuelto'
                                      ? 'bg-emerald-100 text-emerald-900'
                                      : 'bg-stone-100 text-stone-700'
                              }`}
                            >
                              {conv.estado === 'pendiente' && 'Pendiente'}
                              {conv.estado === 'en_atencion' && 'En atención'}
                              {conv.estado === 'resuelto' && 'Resuelto'}
                              {conv.estado === 'bot' && 'Bot IA'}
                            </span>
                          </div>

                          {lastMsg && (
                            <p className="text-xs text-ink/70 line-clamp-2 leading-relaxed">
                              {lastMsg.contenido}
                            </p>
                          )}

                          <div className="mt-2 flex items-center justify-between text-[10px] text-ink/50">
                            <span>
                              {new Date(conv.updated_at || conv.created_at).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                            <span>{conv.messages?.length || 0} msgs</span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Right Column: Active Chat Detail */}
            <div className="col-span-12 md:col-span-8 lg:col-span-8 flex flex-col rounded-3xl bg-white/50 ring-1 ring-black/5 backdrop-blur-md overflow-hidden shadow-sm">
              {selectedConversation ? (
                <>
                  {/* Chat Header */}
                  <div className="flex flex-wrap items-center justify-between border-b border-black/5 bg-white/60 p-4 gap-3">
                    <div className="flex items-center gap-3">
                      <div className="grid size-10 place-items-center rounded-2xl bg-gold/40 font-display font-bold text-ink">
                        {selectedConversation.session_id.slice(-2).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-ink">{selectedConversation.session_id}</span>
                          <span className="rounded-full bg-cream px-2 py-0.5 text-[10px] font-semibold text-ink/70 ring-1 ring-black/5">
                            Idioma: {selectedConversation.idioma || 'es'}
                          </span>
                        </div>
                        <div className="text-xs text-ink/60">
                          Estado: <span className="font-semibold text-ink">{selectedDetails?.estado || selectedConversation.estado}</span>
                          {selectedDetails?.agente_asignado && ` · Atendido por ${selectedDetails.agente_asignado}`}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {selectedDetails?.estado === 'pendiente' && (
                        <button
                          onClick={() => handleClaim(selectedConversation.id)}
                          className="rounded-xl bg-ink px-4 py-2 text-xs font-semibold text-cream shadow-sm hover:bg-ink/90"
                        >
                          Tomar caso
                        </button>
                      )}

                      {selectedDetails?.estado === 'en_atencion' && (
                        <button
                          onClick={() => handleResolve(selectedConversation.id)}
                          className="flex items-center gap-1.5 rounded-xl bg-emerald-700 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-800"
                        >
                          <Check size={14} />
                          <span>Marcar resuelto</span>
                        </button>
                      )}

                      <button
                        onClick={() => handleDelete(selectedConversation.id)}
                        className="grid size-8 place-items-center rounded-xl text-ink/40 hover:bg-rose/50 hover:text-ink"
                        title="Eliminar registro"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>

                  {/* Messages Scroll Area */}
                  <div className="flex-1 space-y-3.5 overflow-y-auto p-5 bg-cream/30">
                    {selectedDetails?.messages && selectedDetails.messages.length > 0 ? (
                      selectedDetails.messages.map((msg, i) => {
                        const isUser = msg.remitente === 'user';
                        const isAgent = msg.remitente === 'agent';
                        const isBot = !isUser && !isAgent;

                        return (
                          <div
                            key={i}
                            className={`flex ${isUser ? 'justify-start' : 'justify-end'}`}
                          >
                            <div
                              className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-xs ${
                                isUser
                                  ? 'bg-white text-ink ring-1 ring-black/10 rounded-tl-xs'
                                  : isAgent
                                    ? 'bg-ink text-cream font-normal rounded-tr-xs ring-1 ring-black/20'
                                    : 'bg-amber-500/10 text-ink rounded-tr-xs ring-1 ring-amber-500/20'
                              }`}
                            >
                              <div className={`mb-1.5 text-[10.5px] font-semibold flex items-center justify-between gap-4 pb-1 border-b ${
                                isAgent ? 'border-white/10 text-gold' : isUser ? 'border-black/5 text-ink/60' : 'border-amber-500/15 text-brand'
                              }`}>
                                <span className="flex items-center gap-1.5">
                                  {isUser ? '👤 Estudiante' : isAgent ? `🧑‍💼 Asesor (${msg.agente || 'Tú'})` : '🤖 Asistente IA'}
                                </span>
                                <span className="opacity-70">
                                  {new Date(msg.timestamp).toLocaleTimeString([], {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                              </div>
                              <FormattedAdvisorMessage text={msg.contenido} isAgent={isAgent} />
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="py-20 text-center text-xs text-ink/40">
                        Cargando historial de mensajes...
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Quick Canned Replies */}
                  <div className="flex flex-wrap gap-1.5 border-t border-black/5 bg-white/40 px-4 py-2">
                    {[
                      '¡Hola! Soy tu asesor Lumina, ¿en qué puedo ayudarte hoy?',
                      'Te comparto que las admisiones para este ciclo cierran este viernes.',
                      'He registrado tu matrícula exitosamente. ¡Bienvenido!'
                    ].map((canned, i) => (
                      <button
                        key={i}
                        onClick={() => setMessageInput(canned)}
                        className="truncate max-w-[260px] rounded-full bg-white/80 px-3 py-1 text-[11px] text-ink/75 ring-1 ring-black/5 hover:bg-white"
                      >
                        {canned}
                      </button>
                    ))}
                  </div>

                  {/* Message Input Bar */}
                  <form onSubmit={handleSendMessage} className="border-t border-black/5 bg-white/80 p-3 flex gap-2">
                    <input
                      type="text"
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      placeholder="Escribe tu respuesta al estudiante..."
                      className="flex-1 rounded-2xl bg-white px-4 py-2.5 text-xs text-ink outline-none ring-1 ring-black/10 focus:ring-2 focus:ring-ink"
                    />
                    <button
                      type="submit"
                      disabled={!messageInput.trim()}
                      className="grid size-10 place-items-center rounded-2xl bg-ink text-cream shadow-xs transition hover:bg-ink/90 disabled:opacity-40"
                    >
                      <Send size={15} />
                    </button>
                  </form>
                </>
              ) : (
                <div className="flex flex-1 flex-col items-center justify-center p-8 text-center text-ink/50">
                  <div className="grid size-14 place-items-center rounded-3xl bg-white/60 ring-1 ring-black/5 mb-4 shadow-xs">
                    <MessageSquare size={24} className="text-brand" />
                  </div>
                  <h3 className="text-base font-semibold text-ink">Selecciona una conversación</h3>
                  <p className="mt-1 max-w-xs text-xs text-ink/60">
                    Escoge un chat de la lista izquierda para revisar el historial y responder al estudiante.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* DOCUMENTS TAB */}
        {activeTab === 'documents' && (
          <div className="space-y-6 animate-rise">
            {/* Header / Intro */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-xs uppercase tracking-[0.2em] text-brand font-semibold">Knowledge Base RAG</span>
                <h2 className="mt-1 text-2xl font-light font-display text-ink">Gestión de Documentos y Base de Conocimiento</h2>
                <p className="mt-1 text-xs text-ink/70 max-w-2xl">
                  Sube y gestiona archivos PDF, Word (.docx) o texto plano. Cada documento se procesa automáticamente y se indexa vectorialmente en ChromaDB para alimentar las respuestas del asistente de IA.
                </p>
              </div>
              <button
                onClick={loadDocList}
                disabled={docsLoading}
                className="self-start sm:self-auto flex items-center gap-1.5 rounded-2xl bg-white/60 px-4 py-2 text-xs font-semibold text-ink ring-1 ring-black/5 hover:bg-white transition"
              >
                <RefreshCw size={13} className={docsLoading ? 'animate-spin' : ''} />
                <span>Actualizar Lista</span>
              </button>
            </div>

            {/* Notifications */}
            {uploadSuccess && (
              <div className="rounded-2xl bg-emerald-100 p-3.5 text-xs text-emerald-900 ring-1 ring-emerald-200 flex items-center justify-between">
                <span>{uploadSuccess}</span>
                <button onClick={() => setUploadSuccess(null)} className="text-emerald-700 hover:text-emerald-900 text-xs font-bold ml-2">✕</button>
              </div>
            )}
            {uploadError && (
              <div className="rounded-2xl bg-rose/60 p-3.5 text-xs text-ink ring-1 ring-rose/80 flex items-center justify-between">
                <span>{uploadError}</span>
                <button onClick={() => setUploadError(null)} className="text-rose-700 hover:text-rose-900 text-xs font-bold ml-2">✕</button>
              </div>
            )}

            <div className="grid grid-cols-12 gap-8">
              {/* Upload Card */}
              <div className="col-span-12 lg:col-span-5">
                <div className="rounded-3xl bg-white/50 p-6 ring-1 ring-black/5 backdrop-blur-md shadow-sm h-full flex flex-col justify-between">
                  <div>
                    <h3 className="text-base font-semibold text-ink mb-1">Subir Nuevo Documento</h3>
                    <p className="text-xs text-ink/70 mb-4">
                      Formatos compatibles: <strong>PDF</strong>, <strong>Word (.docx)</strong>, TXT y MD.
                    </p>

                    <form onSubmit={handleUploadDocument} className="space-y-4">
                      <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-black/15 bg-white/40 p-6 text-center transition hover:bg-white/70">
                        <Upload size={32} className="text-brand mb-2" />
                        <label className="cursor-pointer text-xs font-semibold text-ink">
                          <span className="rounded-xl bg-ink/5 px-3 py-1.5 text-ink hover:bg-ink/10">Seleccionar PDF / Word / TXT</span>
                          <input
                            type="file"
                            accept=".pdf,.docx,.doc,.txt,.md"
                            onChange={(e) => setUploadFile(e.target.files[0] || null)}
                            className="hidden"
                          />
                        </label>
                        {uploadFile ? (
                          <div className="mt-3 flex flex-col items-center gap-1">
                            <span className="text-xs font-bold text-emerald-900 bg-emerald-100 px-3 py-1 rounded-full">
                              {uploadFile.name}
                            </span>
                            <span className="text-[10.5px] text-ink/60">
                              ({(uploadFile.size / 1024).toFixed(1)} KB)
                            </span>
                          </div>
                        ) : (
                          <span className="mt-2 text-[11px] text-ink/50">o arrastra el archivo aquí</span>
                        )}
                      </div>

                      <div className="flex items-center justify-center gap-2 pt-1 text-[11px] text-ink/60">
                        <span className="rounded bg-rose/60 px-1.5 py-0.5 font-bold text-rose-900">PDF</span>
                        <span className="rounded bg-sky-100 px-1.5 py-0.5 font-bold text-sky-900">DOCX</span>
                        <span className="rounded bg-black/5 px-1.5 py-0.5 font-medium text-ink/70">TXT / MD</span>
                      </div>

                      <button
                        type="submit"
                        disabled={!uploadFile || uploadLoading}
                        className="flex w-full items-center justify-center gap-2 rounded-2xl bg-ink py-3 text-xs font-semibold text-cream shadow-sm hover:bg-ink/90 disabled:opacity-50 transition"
                      >
                        {uploadLoading && <Loader2 size={14} className="animate-spin" />}
                        <span>{uploadLoading ? 'Extrayendo texto e indexando en ChromaDB...' : 'Subir e Indexar a Base RAG'}</span>
                      </button>
                    </form>
                  </div>

                  <div className="mt-6 rounded-2xl bg-white/40 p-3.5 ring-1 ring-black/5 text-[11.5px] text-ink/75 leading-relaxed">
                    💡 <strong>Tip para documentos Word y PDF:</strong> Asegúrate de que las secciones principales contengan tablas de aranceles, fechas y programas claramente estructurados.
                  </div>
                </div>
              </div>

              {/* Documents List & CRUD */}
              <div className="col-span-12 lg:col-span-7">
                <div className="rounded-3xl bg-white/50 p-6 ring-1 ring-black/5 backdrop-blur-md shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-semibold text-ink">Documentos en la Base RAG</h3>
                      <span className="rounded-full bg-brand/10 px-2.5 py-0.5 text-xs font-bold text-brand">
                        {documents.length} archivos
                      </span>
                    </div>
                  </div>

                  {docsLoading ? (
                    <div className="flex flex-col items-center justify-center py-12 text-ink/50">
                      <Loader2 size={24} className="animate-spin text-brand mb-2" />
                      <span className="text-xs">Cargando base de conocimiento...</span>
                    </div>
                  ) : documents.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-black/15 p-8 text-center text-ink/60 text-xs">
                      No hay documentos cargados en la base de datos RAG. Sube un archivo PDF o Word para empezar.
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
                      {documents.map((doc) => {
                        const isDeleting = deletingDoc === doc.filename;
                        const ext = doc.extension?.toLowerCase() || '';
                        const isPdf = ext === 'pdf';
                        const isDocx = ext === 'docx' || ext === 'doc';

                        return (
                          <div
                            key={doc.filename}
                            className="flex items-center justify-between gap-3 rounded-2xl bg-white/80 p-4 ring-1 ring-black/5 hover:bg-white transition shadow-xs"
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <div
                                className={`grid size-10 shrink-0 place-items-center rounded-2xl text-[10px] font-bold ring-1 ${
                                  isPdf
                                    ? 'bg-rose/70 text-rose-950 ring-rose/50'
                                    : isDocx
                                    ? 'bg-sky-100 text-sky-950 ring-sky-200'
                                    : 'bg-black/5 text-ink ring-black/10'
                                }`}
                              >
                                {isPdf ? 'PDF' : isDocx ? 'DOCX' : 'TXT'}
                              </div>
                              <div className="min-w-0">
                                <div className="text-xs font-semibold text-ink truncate">
                                  {doc.filename}
                                </div>
                                <div className="text-[11px] text-ink/60 flex items-center gap-2 mt-0.5">
                                  <span>{doc.size_formatted}</span>
                                  <span>•</span>
                                  <span>{new Date(doc.updated_at).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                                </div>
                              </div>
                            </div>

                            <button
                              onClick={() => handleDeleteDoc(doc.filename)}
                              disabled={isDeleting}
                              title="Eliminar documento e indexación"
                              className="grid size-9 shrink-0 place-items-center rounded-xl bg-white/60 text-rose-700 hover:bg-rose-100 hover:text-rose-900 ring-1 ring-black/5 transition disabled:opacity-50"
                            >
                              {isDeleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={15} />}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* METRICS TAB */}
        {activeTab === 'metrics' && (
          <div className="space-y-6 animate-rise">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs uppercase tracking-[0.2em] text-ink/50 font-semibold">Dashboard Ejecutivo</span>
                <h2 className="mt-1 text-2xl font-light font-display text-ink">Métricas del Sistema y SLA</h2>
              </div>
              <button
                onClick={() => loadMetrics(true)}
                disabled={metricsLoading}
                className="flex items-center gap-1.5 rounded-2xl bg-white/60 px-4 py-2 text-xs font-semibold text-ink ring-1 ring-black/5 hover:bg-white disabled:opacity-60 transition cursor-pointer"
              >
                <RefreshCw size={13} className={metricsLoading ? 'animate-spin text-brand' : ''} />
                <span>{metricsLoading ? 'Actualizando...' : 'Actualizar'}</span>
              </button>
            </div>

            {/* Metrics Cards Grid */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-3xl bg-white/50 p-6 ring-1 ring-black/5 backdrop-blur-md shadow-xs">
                <span className="text-xs text-ink/60 font-medium">Resolución por IA</span>
                <div className="mt-2 text-3xl font-light font-display text-ink">
                  {metrics?.ai_resolution_rate_pct ?? '100'}%
                </div>
                <div className="mt-1 text-[11px] text-emerald-800 font-medium">Atención inmediata sin esperas</div>
              </div>

              <div className="rounded-3xl bg-white/50 p-6 ring-1 ring-black/5 backdrop-blur-md shadow-xs">
                <span className="text-xs text-ink/60 font-medium">Cumplimiento SLA</span>
                <div className="mt-2 text-3xl font-light font-display text-gold">
                  {metrics?.sla_compliance_pct ?? '100'}%
                </div>
                <div className="mt-1 text-[11px] text-ink/60">Tiempo de respuesta &lt; 10 min</div>
              </div>

              <div className="rounded-3xl bg-white/50 p-6 ring-1 ring-black/5 backdrop-blur-md shadow-xs">
                <span className="text-xs text-ink/60 font-medium">Ahorro Estimado LPU</span>
                <div className="mt-2 text-3xl font-light font-display text-brand">
                  {metrics?.cost_saved_usd ?? '$0.00 USD'}
                </div>
                <div className="mt-1 text-[11px] text-ink/60">Optimización de caché de tokens</div>
              </div>

              <div className="rounded-3xl bg-white/50 p-6 ring-1 ring-black/5 backdrop-blur-md shadow-xs">
                <span className="text-xs text-ink/60 font-medium">Total Conversaciones</span>
                <div className="mt-2 text-3xl font-light font-display text-ink">
                  {metrics?.db_stats?.total_conversations ?? conversations.length}
                </div>
                <div className="mt-1 text-[11px] text-ink/60">
                  {metrics?.db_stats?.pending_conversations ?? 0} pendientes de atención
                </div>
              </div>
            </div>

            {/* Language Distribution & DB Stats */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="rounded-3xl bg-white/40 p-6 ring-1 ring-black/5 backdrop-blur-sm">
                <h3 className="text-sm font-semibold text-ink mb-4">Distribución por Idioma</h3>
                <div className="space-y-3">
                  {[
                    { lang: 'Español (es)', count: metrics?.db_stats?.languages?.es ?? 0, color: 'bg-brand' },
                    { lang: 'Inglés (en)', count: metrics?.db_stats?.languages?.en ?? 0, color: 'bg-gold' },
                    { lang: 'Francés (fr)', count: metrics?.db_stats?.languages?.fr ?? 0, color: 'bg-rose' },
                    { lang: 'Portugués (pt)', count: metrics?.db_stats?.languages?.pt ?? 0, color: 'bg-accent-rose' }
                  ].map((item) => (
                    <div key={item.lang} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className={`size-2.5 rounded-full ${item.color}`} />
                        <span className="text-ink/80">{item.lang}</span>
                      </div>
                      <span className="font-semibold text-ink">{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-3xl bg-white/40 p-6 ring-1 ring-black/5 backdrop-blur-sm">
                <h3 className="text-sm font-semibold text-ink mb-4">Estado de la Base de Datos</h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between border-b border-black/5 pb-2">
                    <span className="text-ink/60">Total Mensajes Procesados</span>
                    <span className="font-bold text-ink">{metrics?.db_stats?.total_messages ?? 0}</span>
                  </div>
                  <div className="flex justify-between border-b border-black/5 pb-2">
                    <span className="text-ink/60">Conversaciones Resueltas</span>
                    <span className="font-bold text-emerald-800">{metrics?.db_stats?.resolved_conversations ?? 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink/60">Latencia Promedio RAG</span>
                    <span className="font-bold text-ink">{(metrics?.avg_rag_latency_seconds ?? 0).toFixed(2)}s</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Custom Confirmation Modal */}
      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm animate-fade">
          <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-2xl ring-1 ring-black/10 animate-rise">
            <div className="flex items-start gap-3.5 mb-3">
              <div className="grid size-11 shrink-0 place-items-center rounded-2xl bg-rose/60 text-rose-800">
                <Trash2 size={20} />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-bold text-ink">{confirmModal.title}</h3>
                <p className="text-xs text-ink/70 mt-1 leading-relaxed">{confirmModal.message}</p>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-2.5">
              <button
                onClick={() => setConfirmModal(null)}
                className="rounded-2xl px-4 py-2 text-xs font-semibold text-ink/70 hover:bg-black/5 transition"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  const fn = confirmModal.onConfirm;
                  setConfirmModal(null);
                  fn();
                }}
                className="rounded-2xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-rose-700 transition"
              >
                {confirmModal.confirmText || 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Floating Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 rounded-2xl bg-ink px-4 py-3 text-xs font-medium text-cream shadow-2xl ring-1 ring-white/15 animate-rise">
          {toast.type === 'error' ? (
            <div className="size-2 rounded-full bg-rose shrink-0" />
          ) : (
            <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
          )}
          <span>{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="ml-2 text-cream/60 hover:text-cream text-xs font-bold"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
