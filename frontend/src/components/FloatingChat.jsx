import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, User, CheckCircle } from 'lucide-react';
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
      showLeadForm: false
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Lead Form States
  const [leadName, setLeadName] = useState('');
  const [leadPhone, setLeadPhone] = useState('');
  const [leadProgram, setLeadProgram] = useState('Inglés');
  const [leadSubmitted, setLeadSubmitted] = useState(false);
  const [activeLeadMessage, setActiveLeadMessage] = useState('');

  const messagesEndRef = useRef(null);
  const inactivityTimerRef = useRef(null);

  // Update initial message when language changes if no conversation started
  useEffect(() => {
    if (messages.length === 1 && messages[0].sender === 'bot') {
      setMessages([
        {
          sender: 'bot',
          text: t('chatInitialGreeting'),
          isEscalated: false,
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

      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: data.response,
          isEscalated: isEscalated,
          showLeadForm: isEscalated
        }
      ]);

      // If out-of-scope, schedule 3-minute inactivity follow-up
      if (isEscalated) {
        setActiveLeadMessage(userText);
        inactivityTimerRef.current = setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              sender: 'bot',
              text: t('chatInactivity'),
              isEscalated: false,
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
          showLeadForm: false
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLeadSubmit = async (e) => {
    e.preventDefault();
    if (!leadName.trim() || !leadPhone.trim()) return;

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
          text: t('chatLeadSuccess', { name: leadName, phone: leadPhone }),
          isEscalated: false,
          showLeadForm: false
        }
      ]);
    } catch (err) {
      alert(language === 'es' ? 'Error enviando tus datos. Por favor intenta de nuevo.' : 'Error sending your data. Please try again.');
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

                {/* Inline Lead Capture Card */}
                {msg.showLeadForm && !leadSubmitted && index === messages.length - 1 && (
                  <div className="chat-lead-card fade-in">
                    <div className="lead-card-header">
                      <User size={16} className="gold-icon" />
                      <span>{t('chatLeadTitle')}</span>
                    </div>

                    <form onSubmit={handleLeadSubmit} className="lead-form">
                      <div className="lead-field">
                        <label>{t('chatFullName')}</label>
                        <input
                          type="text"
                          required
                          placeholder="Ej. Juan Pérez"
                          value={leadName}
                          onChange={(e) => setLeadName(e.target.value)}
                        />
                      </div>

                      <div className="lead-field">
                        <label>{t('chatPhone')}</label>
                        <input
                          type="tel"
                          required
                          placeholder="Ej. 3001234567"
                          value={leadPhone}
                          onChange={(e) => setLeadPhone(e.target.value)}
                        />
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

                      <button type="submit" className="btn-lead-submit" disabled={loading}>
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

          <form className="chat-footer" onSubmit={handleSend}>
            <input
              type="text"
              className="chat-input"
              placeholder={t('chatPlaceholder')}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="chat-send-btn" disabled={loading || !input.trim()}>
              <Send size={18} />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
