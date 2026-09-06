import React from 'react';
import { BookOpen, Mail, Phone, MapPin } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function Footer({ onNavigateToAdmin }) {
  const { t } = useLanguage();

  return (
    <footer className="footer-container">
      <div className="footer-content">
        <div className="footer-brand">
          <div className="logo">
            <div className="logo-icon">
              <BookOpen size={20} />
            </div>
            <span className="logo-text">Academia <span className="highlight">Lumina</span></span>
          </div>
          <p className="footer-tagline">
            {t('footerDesc')}
          </p>
        </div>

        <div className="footer-contacts">
          <div className="contact-row">
            <MapPin size={14} className="gold-icon" />
            <span>Sede Principal, Colombia</span>
          </div>
          <div className="contact-row">
            <Mail size={14} className="gold-icon" />
            <span>admisiones@academialumina.edu.co</span>
          </div>
          <div className="contact-row">
            <Phone size={14} className="gold-icon" />
            <span>+57 (601) 789-0123</span>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>© 2026 Academia Lumina. {t('footerRights')}</p>
        <button 
          onClick={onNavigateToAdmin}
          className="footer-admin-link"
          title="Acceso Asesores Lumina"
        >
          {t('advisorPortal')}
        </button>
      </div>
    </footer>
  );
}
