import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, MessageCircle } from 'lucide-react';
import { sendChatMessage } from '../services/api';

export default function FloatingChat({ isOpen, setIsOpen }) {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: '¡Hola! Soy el asistente virtual de Academia Lumina. ¿En qué te puedo colaborar hoy? Puedes preguntarme sobre precios, horarios, niveles de inglés, francés o portugués e inscripciones.',
      isEscalated: false,
      whatsappLink: null
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');

    // Agregar mensaje del usuario
    setMessages((prev) => [
      ...prev,
      { sender: 'user', text: userText }
    ]);
    setLoading(true);

    try {
      const data = await sendChatMessage(userText);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: data.response,
          isEscalated: data.is_escalated,
          whatsappLink: data.whatsapp_link
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: 'Ocurrió un error al procesar tu solicitud. Por favor intenta de nuevo.',
          isEscalated: false,
          whatsappLink: null
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
          className="chat-bubble-btn"
          onClick={() => setIsOpen(true)}
          title="Abrir Chat de Atención al Cliente"
        >
          <MessageSquare size={28} />
        </button>
      ) : (
        <div className="chat-window">
          <div className="chat-header">
            <span className="chat-header-title">Academia Lumina - Asistente IA</span>
            <button className="chat-close-btn" onClick={() => setIsOpen(false)}>
              <X size={20} />
            </button>
          </div>

          <div className="chat-body">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`message-bubble ${
                  msg.sender === 'user' ? 'message-user' : 'message-bot'
                }`}
              >
                <div>{msg.text}</div>
                {msg.isEscalated && msg.whatsappLink && (
                  <a
                    href={msg.whatsappLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="whatsapp-btn"
                  >
                    <MessageCircle size={18} /> Chatear por WhatsApp
                  </a>
                )}
              </div>
            ))}
            {loading && (
              <div className="message-bubble message-bot">
                Escribiendo respuesta...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-footer" onSubmit={handleSend}>
            <input
              type="text"
              className="chat-input"
              placeholder="Escribe tu consulta aquí..."
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
