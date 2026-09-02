import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, X, Send, Bot, User, Check, AlertCircle } from 'lucide-react';
import { sendChatMessage, sendLeadInfo } from '../services/api';
import { useLanguage } from '../context/LanguageContext';

export default function FloatingChat({ isOpen, setIsOpen }) {
  const { t, language } = useLanguage();
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: t('chatInitialGreeting'),
      isEscalated: false,
      isClosed: false,
      escalationChoice: null
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeLeadMessage, setActiveLeadMessage] = useState('');

  // Lead capture form state
  const [leadName, setLeadName] = useState('');
  const [leadPhone, setLeadPhone] = useState('');
  const [leadProgram, setLeadProgram] = useState('Inglés');
  const [leadSubmitted, setLeadSubmitted] = useState(false);

  // Real-time input validation states
  const [nameTouched, setNameTouched] = useState(false);
  const [phoneTouched, setPhoneTouched] = useState(false);
  const [nameError, setNameError] = useState('');
  const [phoneError, setPhoneError] = useState('');

  const messagesEndRef = useRef(null);
  const inactivityTimerRef = useRef(null);

  // Client-side validation helpers
  const validateName = (val) => {
    const trimmed = val.trim();
    if (!trimmed) return language === 'es' ? 'El nombre es obligatorio.' : 'Name is required.';
    if (trimmed.length < 2) return language === 'es' ? 'Debe tener al menos 2 caracteres.' : 'Must be at least 2 characters.';
    return '';
  };

  const validatePhone = (val) => {
    const trimmed = val.trim().replace(/\D/g, '');
    if (!trimmed) return language === 'es' ? 'El teléfono es obligatorio.' : 'Phone number is required.';
    if (trimmed.length < 7) return language === 'es' ? 'Ingresa al menos 7 dígitos.' : 'Enter at least 7 digits.';
    return '';
  };

  // Helper to format bold markdown and linebreaks
  const formatMessageContent = (content) => {
    if (!content) return null;
    const lines = content.split('\n');

    return (
      <div className="msg-content">
        {lines.map((line, idx) => {
          if (!line.trim()) {
            return <div key={idx} style={{ height: '6px' }} />;
          }

          if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
            const cleanItem = line.trim().substring(2);
            return (
              <li key={idx} className="msg-list-item">
                {renderFormattedText(cleanItem)}
              </li>
            );
          }

          if (/^\d+\.\s/.test(line.trim())) {
            const cleanItem = line.trim().replace(/^\d+\.\s/, '');
            return (
              <li key={idx} className="msg-list-item" style={{ listStyleType: 'decimal' }}>
                {renderFormattedText(cleanItem)}
              </li>
            );
          }

          return (
            <p key={idx} className="msg-paragraph">
              {renderFormattedText(line)}
            </p>
          );
        })}
      </div>
    );
  };

  const renderFormattedText = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={i} className="msg-bold">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });
  };

  // Update initial greeting when language changes if no conversation exists yet
  useEffect(() => {
    if (messages.length === 1 && messages[0].sender === 'bot') {
      setMessages([
        {
          sender: 'bot',
          text: t('chatInitialGreeting'),
          isEscalated: false,
          isClosed: false,
          escalationChoice: null
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

    const newMessages = [
      ...messages,
      { sender: 'user', text: userText }
    ];

    setMessages(newMessages);
    setLoading(true);

    try {
      const cleanHistory = messages.map((m) => ({
        sender: m.sender,
        text: m.text
      }));
      const data = await sendChatMessage(userText, 'web_session_01', language, cleanHistory);
      const isEscalated = data.is_escalated;
      const isClosed = data.is_closed;

      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: data.response,
          isEscalated: isEscalated,
          isClosed: isClosed,
          escalationChoice: isEscalated ? 'pending' : null
        }
      ]);

      // If escalated, record active query for lead form
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
              escalationChoice: null
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
          escalationChoice: null
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleEscalationDecision = (msgIndex, accepted) => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }

    setMessages((prev) => {
      const updated = [...prev];
      if (updated[msgIndex]) {
        updated[msgIndex] = {
          ...updated[msgIndex],
          escalationChoice: accepted ? 'accepted' : 'declined'
        };
      }
      if (!accepted) {
        updated.push({
          sender: 'bot',
          text: t('chatAdvisorDeclined'),
          isEscalated: false,
          isClosed: false,
          escalationChoice: null
        });
      }
      return updated;
    });
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
          escalationChoice: null
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
          escalationChoice: null
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
                            escalationChoice: null
                          }
                        ]);
                      }}
                      type="button"
                    >
                      <span>{language === 'es' ? 'Nueva consulta 💬' : 'New question 💬'}</span>
                    </button>
                  </div>
                )}

                {/* Escalation Yes/No Confirmation Action Controls */}
                {msg.isEscalated && msg.escalationChoice === 'pending' && index === messages.length - 1 && (
                  <div className="chat-escalation-prompt fade-in">
                    <p className="escalation-prompt-text">{t('chatAdvisorPrompt')}</p>
                    <div className="escalation-actions-row">
                      <button 
                        type="button" 
                        className="btn-escalation-choice btn-choice-yes"
                        onClick={() => handleEscalationDecision(index, true)}
                      >
                        <Check size={15} />
                        <span>{t('chatAdvisorYes')}</span>
                      </button>
                      <button 
                        type="button" 
                        className="btn-escalation-choice btn-choice-no"
                        onClick={() => handleEscalationDecision(index, false)}
                      >
                        <X size={15} />
                        <span>{t('chatAdvisorNo')}</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Inline Lead Capture Card with Real-Time Validation (Opens when 'Yes' is clicked) */}
                {msg.isEscalated && msg.escalationChoice === 'accepted' && !leadSubmitted && index === messages.length - 1 && (
                  <div className="chat-lead-card slide-up">
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
                          className="lead-input"
                        />
                        {nameTouched && nameError && (
                          <div className="field-error-msg">
                            <AlertCircle size={12} />
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
                          className="lead-input"
                        />
                        {phoneTouched && phoneError && (
                          <div className="field-error-msg">
                            <AlertCircle size={12} />
                            <span>{phoneError}</span>
                          </div>
                        )}
                      </div>

                      <div className="lead-field">
                        <label>{t('chatProgram')}</label>
                        <select
                          value={leadProgram}
                          onChange={(e) => setLeadProgram(e.target.value)}
                          className="lead-select"
                        >
                          <option value="Inglés">🇬🇧 Inglés</option>
                          <option value="Francés">🇫🇷 Francés</option>
                          <option value="Portugués">🇧🇷 Portugués</option>
                        </select>
                      </div>

                      <button
                        type="submit"
                        className="btn-submit-lead"
                        disabled={loading || (nameTouched && !!nameError) || (phoneTouched && !!phoneError)}
                      >
                        {loading ? (
                          <span>Enviando...</span>
                        ) : (
                          <>
                            <Check size={16} />
                            <span>{t('chatSubmitLead')}</span>
                          </>
                        )}
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
