import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, User, Bot, Sparkles, Loader2, Minimize2, Phone, ArrowRight, ShieldCheck } from 'lucide-react';
import { sendChatMessage, sendLeadInfo, WS_BASE_URL } from '../services/api';

function getOrCreateSessionId() {
  if (typeof window === 'undefined') return 'default';
  let sessionId = sessionStorage.getItem('lumina_session_id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    sessionStorage.setItem('lumina_session_id', sessionId);
  }
  return sessionId;
}

function renderInlineFormatting(text) {
  if (!text) return null;

  // Match bold **text** or *text*
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

function FormattedMessage({ text }) {
  if (!text) return null;

  // Pre-process text: normalize <br>, <br/>, remove raw html artifacts
  const cleanText = text
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/?[bi]>/gi, '')
    .replace(/&nbsp;/gi, ' ');

  const lines = cleanText.split('\n');
  const elements = [];
  let currentList = [];
  let tableRows = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="my-1.5 space-y-1.5 pl-1.5">
          {currentList.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-xs leading-relaxed text-ink/90">
              <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-brand/70" />
              <div className="flex-1">{renderInlineFormatting(item)}</div>
            </li>
          ))}
        </ul>
      );
      currentList = [];
    }
  };

  const flushTable = () => {
    if (tableRows.length > 0) {
      elements.push(
        <div key={`table-${elements.length}`} className="my-2.5 overflow-hidden rounded-xl border border-black/10 bg-white/70 text-xs shadow-xs">
          <div className="divide-y divide-black/5">
            {tableRows.map((row, rIdx) => {
              const isHeader = rIdx === 0 && row.length > 1;
              return (
                <div
                  key={rIdx}
                  className={`p-2.5 ${
                    isHeader
                      ? 'bg-black/5 font-bold text-ink'
                      : 'flex flex-col sm:flex-row sm:items-center justify-between gap-1 hover:bg-black/[0.02]'
                  }`}
                >
                  {row.map((cell, cIdx) => (
                    <span
                      key={cIdx}
                      className={
                        !isHeader && cIdx === 0
                          ? 'font-semibold text-brand min-w-[110px]'
                          : 'text-ink/80'
                      }
                    >
                      {renderInlineFormatting(cell)}
                    </span>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      );
      tableRows = [];
    }
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      flushTable();
      return;
    }

    // Check for markdown table line (| col | col | or I col I col I or |-|-|-|)
    if (/^[|I].*[|I]$/.test(trimmed)) {
      if (/^[|I\-:\s]+$/.test(trimmed)) {
        return; // separator row
      }
      flushList();
      const cells = trimmed
        .split(/[|I]/)
        .map((c) => c.trim())
        .filter((c) => c.length > 0);
      if (cells.length > 0) {
        tableRows.push(cells);
      }
      return;
    } else {
      flushTable();
    }

    // 1. Check if line is a Section / Category Header (e.g. **Modalidades:** or - **Modalidades:** or Modalidades:)
    const boldHeaderMatch = trimmed.match(/^[-*•]?\s*\*\*([^*:\n]+):?\*\*:?$/);
    const mdHeaderMatch = trimmed.match(/^(?:###|##|#)\s+(.+)$/);
    const isColonTitle = !boldHeaderMatch && !mdHeaderMatch && /^[A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúÁÉÍÓÚñÑ\s()/-]{2,45}:$/.test(trimmed) && !trimmed.includes('http');

    if (boldHeaderMatch || mdHeaderMatch || isColonTitle) {
      flushList();
      const headerTitle = boldHeaderMatch ? boldHeaderMatch[1] : mdHeaderMatch ? mdHeaderMatch[1] : trimmed.replace(/:$/, '');
      elements.push(
        <div key={`section-hdr-${index}`} className="mt-3.5 mb-1.5 flex items-center gap-2 border-b border-black/10 pb-1">
          <span className="size-2 rounded-sm bg-brand shrink-0" />
          <span className="text-[11.5px] font-bold uppercase tracking-wider text-ink">
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
        <div key={`quote-${index}`} className="my-2.5 rounded-2xl bg-gold/15 border-l-2 border-brand p-2.5 text-xs text-ink/90 leading-relaxed shadow-xs">
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
      <p key={`p-${index}`} className="my-1 text-xs leading-relaxed text-ink/90">
        {renderInlineFormatting(trimmed)}
      </p>
    );
  });

  flushList();
  flushTable();

  return <div className="space-y-1">{elements}</div>;
}

export default function FloatingChat({ isOpen, setIsOpen }) {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: '¡Hola! Te damos la bienvenida a Academia Lumina. ¿En qué idioma te gustaría formarte hoy?',
      timestamp: Date.now()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState('bot'); // 'bot' | 'pendiente' | 'en_atencion' | 'resuelto'
  const [assignedAgent, setAssignedAgent] = useState(null);
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [lead, setLead] = useState({ name: '', phone: '', program: 'Inglés' });
  const [leadErrors, setLeadErrors] = useState({ name: '', phone: '' });
  const [leadSubmitted, setLeadSubmitted] = useState(false);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const sessionIdRef = useRef(getOrCreateSessionId());
  const statusRef = useRef(status);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isLoading, isOpen, showLeadForm]);

  // WebSocket connection for real-time agent handoff
  useEffect(() => {
    if (!isOpen) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    const sessionId = sessionIdRef.current;
    const wsUrl = `${WS_BASE_URL}/chat/${sessionId}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'status' || data.type === 'session_status') {
              if (data.estado) setStatus(data.estado);
              if (data.status) setStatus(data.status);
              if (data.agente_asignado) setAssignedAgent(data.agente_asignado);
              if (data.agente) setAssignedAgent(data.agente);
              if (Array.isArray(data.messages) && data.messages.length > 0) {
                setMessages((prev) => {
                  // If only default greeting is present or messages were out of sync, sync from server
                  if (prev.length <= 1) {
                    return data.messages.map((m) => ({
                      sender: m.sender,
                      text: m.text,
                      agentName: m.agentName || 'Asesor Lumina',
                      timestamp: m.timestamp ? new Date(m.timestamp).getTime() : Date.now()
                    }));
                  }
                  // Otherwise merge any agent messages not yet in state
                  const currentTexts = new Set(prev.map((m) => `${m.sender}:${m.text}`));
                  const missing = data.messages
                    .filter((m) => !currentTexts.has(`${m.sender}:${m.text}`))
                    .map((m) => ({
                      sender: m.sender,
                      text: m.text,
                      agentName: m.agentName || 'Asesor Lumina',
                      timestamp: m.timestamp ? new Date(m.timestamp).getTime() : Date.now()
                    }));
                  return missing.length > 0 ? [...prev, ...missing] : prev;
                });
              }
            } else if (data.type === 'agent_message' || data.type === 'message') {
              const agentName = data.agent_name || data.agente || assignedAgent || 'Asesor Lumina';
              setStatus('en_atencion');
              setAssignedAgent(agentName);
              setMessages((prev) => [
                ...prev,
                {
                  sender: 'agent',
                  text: data.message || data.text,
                  agentName: agentName,
                  timestamp: Date.now()
                }
              ]);
            } else if (data.type === 'agent_connected') {
              if (statusRef.current === 'resuelto') {
                return;
              }
              const agentName = data.agent_name || 'Asesor Lumina';
              setStatus('en_atencion');
              setAssignedAgent(agentName);
              setMessages((prev) => [
                ...prev,
                {
                  sender: 'agent',
                  text: data.message || `El asesor ${agentName} se ha unido al chat para atenderte.`,
                  agentName: agentName,
                  timestamp: Date.now()
                }
              ]);
            } else if (data.type === 'conversation_resolved') {
              setStatus('resuelto');
              setAssignedAgent(null);
              setMessages((prev) => [
                ...prev,
                {
                  sender: 'bot',
                  text: data.message || 'La conversación ha sido resuelta por el asesor. ¡Gracias por comunicarte con Academia Lumina!',
                  timestamp: Date.now()
                }
              ]);
            }
          } catch (e) {
            console.error('[Lumina Chat WS] Error parseando mensaje:', e);
          }
        };

        ws.onerror = (err) => {
          console.warn('[Lumina Chat WS] WebSocket error (usando fallback HTTP):', err);
        };

        return () => {
          ws.close();
        };
    } catch (e) {
      console.warn('[Lumina Chat WS] Error iniciando conexión:', e);
    }
  }, [isOpen]);

  const handleSend = async (customText = null) => {
    const textToSend = typeof customText === 'string' ? customText : input;
    if (!textToSend.trim() || isLoading) return;

    const userMessage = textToSend.trim();
    setInput('');
    setError(null);

    // Append user message immediately
    const updatedMessages = [
      ...messages,
      { sender: 'user', text: userMessage, timestamp: Date.now() }
    ];
    setMessages(updatedMessages);

    // If currently talking to a live agent, send directly via WebSocket
    if (status === 'en_atencion' || status === 'pendiente') {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'user_message',
          message: userMessage
        }));
        return;
      }
    }

    setIsLoading(true);

    try {
      // Build conversation history for context
      const history = updatedMessages
        .filter((m) => m.sender === 'user' || m.sender === 'bot')
        .map((m) => ({ sender: m.sender, text: m.text }));

      const response = await sendChatMessage(
        userMessage,
        sessionIdRef.current,
        'es',
        history
      );

      // Append bot answer
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: response.response,
          timestamp: Date.now()
        }
      ]);

      if (response.is_escalated) {
        setStatus('pendiente');
        setShowLeadForm(true);
      }

      if (response.is_closed) {
        setStatus('resuelto');
      }
    } catch (err) {
      setError('Lo sentimos, hubo una intermitencia de conexión. Por favor intenta de nuevo.');
    } finally {
      setIsLoading(false);
    }
  };

  const validateLeadForm = () => {
    const errors = { name: '', phone: '' };
    let isValid = true;

    const cleanName = lead.name.trim();
    if (!cleanName || cleanName.length < 2 || !/[a-zA-ZáéíóúÁÉÍÓÚñÑ]{2,}/.test(cleanName)) {
      errors.name = 'Ingresa tu nombre válido (mínimo 2 letras).';
      isValid = false;
    }

    const cleanPhone = lead.phone.trim();
    const digits = cleanPhone.replace(/\D/g, '');
    if (/[a-zA-Z]/.test(cleanPhone)) {
      errors.phone = 'El teléfono no puede contener letras o palabras.';
      isValid = false;
    } else if (digits.length < 7 || digits.length > 15) {
      errors.phone = 'Ingresa un número telefónico o WhatsApp válido (7 a 15 dígitos).';
      isValid = false;
    }

    setLeadErrors(errors);
    return isValid;
  };

  const handleLeadSubmit = async (e) => {
    e.preventDefault();
    if (!validateLeadForm() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      await sendLeadInfo({
        name: lead.name.trim(),
        phone: lead.phone.trim(),
        program: lead.program,
        user_message: messages.map((m) => `${m.sender}: ${m.text}`).join('\n'),
        session_id: sessionIdRef.current,
        language: 'es'
      });

      setLeadSubmitted(true);
      setShowLeadForm(false);
      setStatus('pendiente');

      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: `¡Perfecto, ${lead.name.trim()}! Hemos registrado tu solicitud de contacto. En unos instantes un asesor humano tomará este chat y te brindará toda la orientación.`,
          timestamp: Date.now()
        }
      ]);
    } catch (err) {
      setError(err.message || 'No pudimos registrar tus datos. Por favor verifica los campos.');
    } finally {
      setIsLoading(false);
    }
  };

  const quickOptions = [
    'Información de Inglés',
    'Francés Intensivo',
    'Portugués',
    'Hablar con un asesor humano'
  ];

  return (
    <>
      {/* Floating Entry Trigger Button (Icon only) */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 grid size-14 place-items-center rounded-full bg-ink text-cream shadow-2xl shadow-ink/30 transition-all duration-300 hover:scale-110 hover:bg-ink/90 active:scale-95 group"
          aria-label="Asistente Lumina"
          title="Asistente Lumina"
        >
          <div className="relative">
            <MessageCircle size={24} className="transition-transform group-hover:scale-105" />
            <span className="absolute -top-1 -right-1 size-3 rounded-full bg-emerald-400 ring-2 ring-cream animate-pulse" />
          </div>
        </button>
      )}

      {/* Centered Expanded Modal with Blurred Backdrop */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-md p-4 animate-fade-in">
          <div className="flex h-[82vh] max-h-[750px] w-full max-w-xl flex-col overflow-hidden rounded-3xl bg-cream shadow-2xl ring-1 ring-black/10 animate-rise">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-black/5 bg-ink px-6 py-4 text-cream">
              <div className="flex items-center gap-3.5">
                <div className="grid size-10 place-items-center rounded-2xl bg-cream/10 ring-1 ring-cream/20">
                  <span className="font-display text-base font-bold text-gold">L</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold tracking-tight">Asistente Lumina</span>
                    <span className="rounded-full bg-gold/20 px-2 py-0.5 text-[10px] font-medium text-gold">
                      Oficial AI
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-cream/75 mt-0.5">
                    <span
                      className={`size-2 rounded-full ${
                        status === 'bot'
                          ? 'bg-emerald-400'
                          : status === 'en_atencion'
                            ? 'bg-gold animate-pulse'
                            : status === 'pendiente'
                              ? 'bg-amber-400 animate-pulse'
                              : 'bg-emerald-400'
                      }`}
                    />
                    <span>
                      {status === 'bot' && 'En línea · Respuestas con IA'}
                      {status === 'pendiente' && 'Asesor en camino · En espera'}
                      {status === 'en_atencion' && `Asesor conectado: ${assignedAgent || 'Asesor Lumina'}`}
                      {status === 'resuelto' && 'Caso resuelto'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsOpen(false)}
                  className="grid size-8 place-items-center rounded-full text-cream/70 transition hover:bg-cream/10 hover:text-cream"
                  title="Minimizar"
                >
                  <Minimize2 size={16} />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="grid size-8 place-items-center rounded-full text-cream/70 transition hover:bg-cream/10 hover:text-cream"
                  title="Cerrar"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 space-y-3.5 overflow-y-auto p-5 md:p-6 bg-cream/60">
              {messages
                .filter((msg) => msg.sender !== 'system' && !msg.text?.startsWith('[Lead Registrado]') && !msg.text?.startsWith('Lead de contacto registrado:'))
                .map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className="flex max-w-[85%] items-start gap-2.5">
                    {msg.sender !== 'user' && (
                      <div
                        className={`mt-1 grid size-7 shrink-0 place-items-center rounded-full text-xs font-semibold ${
                          msg.sender === 'agent'
                            ? 'bg-gold text-ink'
                            : 'bg-ink text-cream'
                        }`}
                      >
                        {msg.sender === 'agent' ? 'A' : 'AI'}
                      </div>
                    )}
                    <div
                      className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-ink text-cream rounded-br-xs shadow-sm'
                          : msg.sender === 'agent'
                            ? 'bg-gold/30 text-ink rounded-bl-xs ring-1 ring-gold/40'
                            : 'bg-white/85 text-ink rounded-bl-xs ring-1 ring-black/5 shadow-xs'
                      }`}
                    >
                      {msg.sender === 'agent' && (
                        <div className="mb-1 text-[11px] font-semibold text-brand">
                          {msg.agentName || 'Asesor Lumina'}
                        </div>
                      )}
                      {msg.sender === 'user' ? (
                        <p className="whitespace-pre-wrap">{msg.text}</p>
                      ) : (
                        <FormattedMessage text={msg.text} />
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2.5 rounded-2xl bg-white/80 px-4 py-2.5 text-xs text-ink/75 ring-1 ring-black/5 shadow-xs">
                    <Loader2 size={14} className="animate-spin text-brand" />
                    <span>El asistente está escribiendo...</span>
                  </div>
                </div>
              )}

              {/* Inline Lead Capture Card when Escalation is Suggested */}
              {showLeadForm && !leadSubmitted && (
                <div className="rounded-2xl bg-white/90 p-5 ring-1 ring-brand/30 shadow-md">
                  <div className="flex items-center gap-2 text-xs font-semibold text-brand">
                    <Phone size={14} />
                    <span>Conectar con un asesor humano</span>
                  </div>
                  <p className="mt-1 text-xs text-ink/70">
                    Déjanos tu nombre y número telefónico para transferirte de inmediato con un asesor:
                  </p>
                  <form onSubmit={handleLeadSubmit} className="mt-3 space-y-3">
                    <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                      <div>
                        <input
                          type="text"
                          value={lead.name}
                          onChange={(e) => {
                            setLead({ ...lead, name: e.target.value });
                            if (leadErrors.name) setLeadErrors((prev) => ({ ...prev, name: '' }));
                          }}
                          placeholder="Tu nombre completo"
                          className={`w-full rounded-xl bg-cream/80 px-3 py-2 text-xs text-ink outline-none ring-1 transition ${
                            leadErrors.name
                              ? 'ring-2 ring-rose/70 bg-rose/[0.04]'
                              : 'ring-black/10 focus:ring-2 focus:ring-ink'
                          }`}
                          required
                        />
                        {leadErrors.name && (
                          <p className="mt-1 text-[11px] font-medium text-rose">
                            {leadErrors.name}
                          </p>
                        )}
                      </div>
                      <div>
                        <input
                          type="tel"
                          value={lead.phone}
                          onChange={(e) => {
                            setLead({ ...lead, phone: e.target.value });
                            if (leadErrors.phone) setLeadErrors((prev) => ({ ...prev, phone: '' }));
                          }}
                          placeholder="Número de WhatsApp (ej. 3001234567)"
                          className={`w-full rounded-xl bg-cream/80 px-3 py-2 text-xs text-ink outline-none ring-1 transition ${
                            leadErrors.phone
                              ? 'ring-2 ring-rose/70 bg-rose/[0.04]'
                              : 'ring-black/10 focus:ring-2 focus:ring-ink'
                          }`}
                          required
                        />
                        {leadErrors.phone && (
                          <p className="mt-1 text-[11px] font-medium text-rose">
                            {leadErrors.phone}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <button
                        type="button"
                        onClick={() => setShowLeadForm(false)}
                        className="text-xs text-ink/50 hover:text-ink"
                      >
                        Continuar con IA
                      </button>
                      <button
                        type="submit"
                        disabled={isLoading}
                        className="inline-flex items-center gap-1.5 rounded-xl bg-ink px-4 py-2 text-xs font-medium text-cream shadow-sm hover:bg-ink/90 disabled:opacity-60"
                      >
                        <span>Pasar con asesor</span>
                        <ArrowRight size={12} />
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {error && (
                <div className="rounded-xl bg-rose/40 px-3.5 py-2 text-xs text-ink/80 ring-1 ring-black/5">
                  {error}
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Suggestion Chips */}
            {messages.length <= 2 && status === 'bot' && (
              <div className="flex flex-wrap gap-2 border-t border-black/5 bg-white/40 px-5 py-2.5">
                {quickOptions.map((opt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(opt)}
                    className="rounded-full bg-white/70 px-3 py-1 text-xs font-medium text-ink/80 ring-1 ring-black/5 transition hover:bg-white hover:text-ink"
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}

            {/* Footer Input Bar */}
            <div className="border-t border-black/5 bg-white/70 p-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Escribe tu consulta sobre programas o admisiones..."
                  className="flex-1 rounded-2xl bg-white px-4 py-3 text-sm text-ink outline-none ring-1 ring-black/10 transition focus:ring-2 focus:ring-ink placeholder:text-ink/40"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  className="grid size-11 place-items-center rounded-2xl bg-ink text-cream shadow-sm transition hover:bg-ink/90 active:scale-95 disabled:opacity-40"
                >
                  <Send size={16} />
                </button>
              </form>
              <div className="mt-2 flex items-center justify-between text-[11px] text-ink/50 px-1">
                <span>Academia Lumina · Asistente Lumina</span>
                <span className="flex items-center gap-1">
                  <ShieldCheck size={12} className="text-brand" />
                  Atención oficial y confidencial
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
