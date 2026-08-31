import React from 'react';
import { BookOpen, Sparkles, Home, Layers, Sun, Moon, Globe } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useTheme } from '../context/ThemeContext';

export default function Navbar({ activeTab, setActiveTab, onOpenChat }) {
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

        {/* Action Controls: Language Toggle + Theme Switcher + AI Assistant Trigger */}
        <div className="nav-actions">
          {/* Language Switcher Button (Phase 4) */}
          <button
            className="btn-control-toggle"
            onClick={toggleLanguage}
            title={language === 'en' ? 'Cambiar a Español' : 'Switch to English'}
            aria-label="Toggle language"
          >
            <Globe size={16} />
            <span className="lang-code">{language === 'en' ? 'ES' : 'EN'}</span>
          </button>

          {/* Theme Toggle Button (Phase 5) */}
          <button
            className="btn-control-toggle"
            onClick={toggleTheme}
            title={theme === 'light' ? 'Activar Modo Oscuro' : 'Activate Light Mode'}
            aria-label="Toggle dark/light theme"
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>

          {/* Chat Open Button */}
          <button className="nav-chat-btn" onClick={onOpenChat}>
            <Sparkles size={16} />
            <span>{t('aiAssistant')}</span>
          </button>
        </div>
      </nav>
    </header>
  );
}
