import React from 'react';
import { Bot, Sparkles, MessageCircle } from 'lucide-react';

export default function FinalCtaSection({ onOpenChat }) {
  return (
    <section className="section-container" id="contacto">
      <div className="final-cta-card">
        <div className="cta-glow-bg"></div>
        <div className="final-cta-content">
          <div className="final-cta-badge">
            <Sparkles size={16} />
            <span>Asistencia Inmediata sin Esperas</span>
          </div>

          <h2 className="final-cta-title">
            ¿Listo para comenzar tu próximo idioma?
          </h2>

          <p className="final-cta-desc">
            Habla con nuestro asistente inteligente y encuentra el programa, nivel y horario ideal para ti en segundos.
          </p>

          <div className="final-cta-buttons">
            <button className="btn-primary-glow btn-lg" onClick={onOpenChat}>
              <Bot size={22} />
              <span>Consultar con el asistente</span>
            </button>

            <a
              href="https://wa.me/573247836387"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-whatsapp-outline"
            >
              <MessageCircle size={20} />
              <span>Hablar con un asesor por WhatsApp</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
