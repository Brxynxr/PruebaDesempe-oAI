import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, User, CheckCircle, AlertCircle, Check } from 'lucide-react';
import { sendChatMessage, sendLeadInfo } from '../services/api';
import { useLanguage } from '../context/LanguageContext';

function formatMessageContent(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let currentList = [];

  const parseInline = (str) => {
    const parts = str.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="msg-bold">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      currentList.push(
        <li key={index} className="msg-list-item">
          {parseInline(trimmed.slice(2))}
        </li>
      );
    } else {
      if (currentList.length > 0) {
        elements.push(
          <ul key={`list-${index}`} className="msg-list">
            {currentList}
          </ul>
        );
        currentList = [];
      }
      if (trimmed) {
        elements.push(
          <p key={index} className="msg-paragraph">
            {parseInline(line)}
          </p>
        );
      }
    }
  });

  if (currentList.length > 0) {
    elements.push(
      <ul key="list-end" className="msg-list">
        {currentList}
      </ul>
    );
  }

  return elements.length > 0 ? elements : text;
}

export default function FloatingChat({ isOpen, setIsOpen }) {
  const { t, language } = useLanguage();
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: t('chatInitialGreeting'),
      isEscalated: false,
      isClosed: false,
      showLeadForm: false
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Lead Form States & Validation
  const [leadName, setLeadName] = useState('');
  const [leadPhone, setLeadPhone] = useState('');
  const [leadProgram, setLeadProgram] = useState('Inglés');
  const [leadSubmitted, setLeadSubmitted] = useState(false);
  const [activeLeadMessage, setActiveLeadMessage] = useState('');

  // Touched and Error states
  const [nameTouched, setNameTouched] = useState(false);
  const [phoneTouched, setPhoneTouched] = useState(false);
  const [nameError, setNameError] = useState('');
  const [phoneError, setPhoneError] = useState('');

  const messagesEndRef = useRef(null);
  const inactivityTimerRef = useRef(null);

  // Validation functions
  const validateName = (name) => {
    const trimmed = name.trim();
    if (!trimmed) {
      return language === 'es' ? 'El nombre completo es requerido.' : 'Full name is required.';
    }
    if (trimmed.length < 3) {
      return language === 'es' ? 'El nombre debe tener al menos 3 caracteres.' : 'Name must be at least 3 characters.';
    }
    if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]+$/.test(trimmed)) {
      return language === 'es' ? 'El nombre solo debe contener letras.' : 'Name must only contain letters.';
    }
    return '';
  };

  const validatePhone = (phone) => {
    const trimmed = phone.trim();
    if (!trimmed) {
      return language === 'es' ? 'El número de WhatsApp o teléfono es requerido.' : 'WhatsApp or phone number is required.';
    }
    const digitsOnly = trimmed.replace(/\D/g, '');
    if (digitsOnly.length < 7 || digitsOnly.length > 15) {
      return language === 'es' 
        ? 'Ingresa un número válido de 10 dígitos (ej. 300 123 4567).' 
        : 'Enter a valid phone number (7-15 digits).';
    }
    return '';
  };

  // Update initial message when language changes if no conversation started
  useEffect(() => {
    if (messages.length === 1 && messages[0].sender === 'bot') {
      setMessages([
        {
          sender: 'bot',
          text: t('chatInitialGreeting'),
          isEscalated: false,
          isClosed: false,
          showLeadForm: false
        }
      ]);
    }
  }, [language]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, leadSubmitted]);

  useEffect(() => {
    return () => {
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current);
      }
    };
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }

    const userText = input.trim();
    setInput('');

    setMessages((prev) => [
      ...prev,
      { sender: 'user', text: userText }
    ]);
    setLoading(true);

    try {
      const data = await sendChatMessage(userText, 'web_session_01', language);
      const isEscalated = data.is_escalated;
      const isClosed = data.is_closed;

      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: data.response,
          isEscalated: isEscalated,
          isClosed: isClosed,
          showLeadForm: isEscalated
        }
      ]);

      // If out-of-scope, schedule 3-minute inactivity follow-up only if not closed
      if (isEscalated && !isClosed) {
        setActiveLeadMessage(userText);
        inactivityTimerRef.current = setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              sender: 'bot',
              text: t('chatInactivity'),
              isEscalated: false,
              isClosed: false,
              showLeadForm: false
            }
          ]);
        }, 180000); // 3 Minutes
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: language === 'es' 
            ? 'Ocurrió un error al procesar tu solicitud. Por favor intenta de nuevo.'
            : 'An error occurred while processing your request. Please try again.',
          isEscalated: false,
          isClosed: false,
          showLeadForm: false
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLeadSubmit = async (e) => {
    e.preventDefault();
    setNameTouched(true);
    setPhoneTouched(true);

    const nErr = validateName(leadName);
    const pErr = validatePhone(leadPhone);
    setNameError(nErr);
    setPhoneError(pErr);

    if (nErr || pErr) {
      return;
    }

    setLoading(true);
    try {
      await sendLeadInfo({
        name: leadName.trim(),
        phone: leadPhone.trim(),
        program: leadProgram,
        user_message: activeLeadMessage || 'Consulta desde el chat web',
        session_id: 'web_session_01',
        language: language
      });

      setLeadSubmitted(true);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: t('chatLeadSuccess', { name: leadName.trim(), phone: leadPhone.trim() }),
          isEscalated: false,
          isClosed: false,
          showLeadForm: false
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: language === 'es' 
            ? '⚠️ Hubo un inconveniente al enviar tus datos. Por favor verifica tu conexión e inténtalo de nuevo.' 
            : '⚠️ There was an issue submitting your details. Please check your connection and try again.',
          isEscalated: false,
          isClosed: false,
          showLeadForm: false
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="floating-chat-container">
      {!isOpen ? (
        <button
          className="chat-bubble-btn pulse-glow"
          onClick={() => setIsOpen(true)}
          title={t('aiAssistant')}
          aria-label="Open AI Customer Support Chat"
        >
          <MessageSquare size={28} />
        </button>
      ) : (
        <div className="chat-window scale-in">
          <div className="chat-header">
            <span className="chat-header-title">{t('chatHeader')}</span>
            <button 
              className="chat-close-btn" 
              onClick={() => setIsOpen(false)}
              aria-label="Close Chat"
            >
              <X size={20} />
            </button>
          </div>

          <div className="chat-body">
            {messages.map((msg, index) => (
              <React.Fragment key={index}>
                <div
                  className={`message-bubble ${
                    msg.sender === 'user' ? 'message-user slide-up' : 'message-bot slide-up'
                  }`}
                >
                  <div className="msg-content">{formatMessageContent(msg.text)}</div>
                </div>

                {/* Closing / Farewell Quick Action Controls */}
                {msg.isClosed && index === messages.length - 1 && (
                  <div className="chat-closing-controls fade-in">
                    <button 
                      className="btn-chat-action close-action" 
                      onClick={() => setIsOpen(false)}
                      type="button"
                    >
                      <X size={14} />
                      <span>{language === 'es' ? 'Cerrar chat' : 'Close chat'}</span>
                    </button>
                    <button 
                      className="btn-chat-action restart-action" 
                      onClick={() => {
                        setMessages([
                          {
                            sender: 'bot',
                            text: t('chatInitialGreeting'),
                            isEscalated: false,
                            isClosed: false,
                            showLeadForm: false
                          }
                        ]);
                      }}
                      type="button"
                    >
                      <span>{language === 'es' ? 'Nueva consulta 💬' : 'New question 💬'}</span>
                    </button>
                  </div>
                )}

                {/* Inline Lead Capture Card with Real-Time Validation */}
                {msg.showLeadForm && !leadSubmitted && index === messages.length - 1 && (
                  <div className="chat-lead-card fade-in">
                    <div className="lead-card-header">
                      <User size={16} className="gold-icon" />
                      <span>{t('chatLeadTitle')}</span>
                    </div>

                    <form onSubmit={handleLeadSubmit} className="lead-form" noValidate>
                      <div className={`lead-field ${nameTouched && (nameError ? 'has-error' : 'is-valid')}`}>
                        <div className="field-label-row">
                          <label>{t('chatFullName')}</label>
                          {nameTouched && !nameError && <Check size={14} className="valid-icon" />}
                        </div>
                        <input
                          type="text"
                          required
                          placeholder="Ej. Juan Pérez"
                          value={leadName}
                          onChange={(e) => {
                            const val = e.target.value;
                            setLeadName(val);
                            if (nameTouched) setNameError(validateName(val));
                          }}
                          onBlur={() => {
                            setNameTouched(true);
                            setNameError(validateName(leadName));
                          }}
                          className={nameTouched && nameError ? 'input-invalid' : (nameTouched && !nameError ? 'input-valid' : '')}
                        />
                        {nameTouched && nameError && (
                          <div className="lead-error-msg slide-up">
                            <AlertCircle size={13} />
                            <span>{nameError}</span>
                          </div>
                        )}
                      </div>

                      <div className={`lead-field ${phoneTouched && (phoneError ? 'has-error' : 'is-valid')}`}>
                        <div className="field-label-row">
                          <label>{t('chatPhone')}</label>
                          {phoneTouched && !phoneError && <Check size={14} className="valid-icon" />}
                        </div>
                        <input
                          type="tel"
                          required
                          placeholder="Ej. 3001234567 o +57 300 123 4567"
                          value={leadPhone}
                          onChange={(e) => {
                            const val = e.target.value;
                            setLeadPhone(val);
                            if (phoneTouched) setPhoneError(validatePhone(val));
                          }}
                          onBlur={() => {
                            setPhoneTouched(true);
                            setPhoneError(validatePhone(leadPhone));
                          }}
                          className={phoneTouched && phoneError ? 'input-invalid' : (phoneTouched && !phoneError ? 'input-valid' : '')}
                        />
                        {phoneTouched && phoneError && (
                          <div className="lead-error-msg slide-up">
                            <AlertCircle size={13} />
                            <span>{phoneError}</span>
                          </div>
                        )}
                      </div>

                      <div className="lead-field">
                        <label>{t('chatProgram')}</label>
                        <select
                          value={leadProgram}
                          onChange={(e) => setLeadProgram(e.target.value)}
                        >
                          <option value="Inglés">🇬🇧 {t('english')}</option>
                          <option value="Francés">🇫🇷 {t('french')}</option>
                          <option value="Portugués">🇧🇷 {t('portuguese')}</option>
                        </select>
                      </div>

                      <button 
                        type="submit" 
                        className="btn-lead-submit" 
                        disabled={loading}
                      >
                        <CheckCircle size={16} />
                        <span>{t('chatSubmitLead')}</span>
                      </button>
                    </form>
                  </div>
                )}
              </React.Fragment>
            ))}

            {/* Animated Typing Indicator */}
            {loading && (
              <div className="message-bubble message-bot typing-indicator fade-in">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSend} className="chat-input-wrapper">
            <input
              type="text"
              placeholder={t('chatPlaceholder')}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="chat-input"
              disabled={loading}
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={!input.trim() || loading}
              aria-label="Send Message"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
