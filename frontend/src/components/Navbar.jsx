import React from 'react';
import { BookOpen, Sparkles, Home, Layers, Sun, Moon, Globe, LogIn } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

export default function Navbar({ activeTab, setActiveTab, onOpenChat, onNavigateToAdmin }) {
  const { language, toggleLanguage, t } = useLanguage();
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="navbar-container">
      <nav className="navbar">
        <div className="logo" onClick={() => setActiveTab('home')} style={{ cursor: 'pointer' }}>
          <div className="logo-icon">
            <BookOpen size={24} />
          </div>
          <span className="logo-text">Academia <span className="highlight">Lumina</span></span>
        </div>
        
        {/* SPA Tab Navigation (2 Main Views) */}
        <div className="spa-tab-nav">
          <button
            className={`tab-btn ${activeTab === 'home' ? 'active' : ''}`}
            onClick={() => setActiveTab('home')}
          >
            <Home size={18} />
            <span>{t('homeAndPrograms')}</span>
          </button>

          <button
            className={`tab-btn ${activeTab === 'modalities' ? 'active' : ''}`}
            onClick={() => setActiveTab('modalities')}
          >
            <Layers size={18} />
            <span>{t('modalitiesAndCert')}</span>
          </button>
        </div>

        {/* Action Controls: Language Toggle + Theme Switcher + Advisor Portal + AI Assistant */}
        <div className="nav-actions">
          {/* Advisor Portal Login Button */}
          <button
            className="btn-advisor-login"
            onClick={onNavigateToAdmin}
            title={t('advisorPortal')}
            aria-label="Acceso Asesores"
          >
            <LogIn size={15} />
            <span className="advisor-btn-text">{t('advisorPortal')}</span>
          </button>

          {/* Language Switcher Button */}
          <button
            className="btn-control-toggle"
            onClick={toggleLanguage}
            title={language === 'en' ? 'Cambiar a Español' : 'Switch to English'}
            aria-label="Toggle language"
          >
            <Globe size={16} />
            <span className="lang-code">{language === 'en' ? 'ES' : 'EN'}</span>
          </button>

          {/* Theme Toggle Button */}
          <button
            className="btn-control-toggle"
            onClick={toggleTheme}
            title={theme === 'light' ? 'Activar Modo Oscuro' : 'Activate Light Mode'}
            aria-label="Toggle dark/light theme"
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
      </nav>
    </header>
  );
}
