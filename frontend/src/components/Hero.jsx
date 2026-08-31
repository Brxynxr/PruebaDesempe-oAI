import React from 'react';
import { Sparkles, ArrowRight, Award, Users, CheckCircle2 } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function Hero({ onOpenChat }) {
  const { t } = useLanguage();

  return (
    <section className="hero-section">
      <div className="hero-grid">
        <div className="hero-content">
          <div className="badge">
            <Sparkles size={14} className="badge-icon" />
            <span>{t('heroBadge')}</span>
          </div>
          
          <h1 className="hero-title">
            {t('heroTitle')}
          </h1>
          
          <p className="hero-subtitle">
            {t('heroSubtitle')}
          </p>

          <div className="hero-actions">
            <button className="btn-primary" onClick={onOpenChat}>
              <span>{t('heroCtaChat')}</span>
              <ArrowRight size={18} />
            </button>
            <a href="#programas" className="btn-secondary">
              {t('heroCtaPrograms')}
            </a>
          </div>

          <div className="hero-stats">
            <div className="stat-card">
              <div className="stat-number">1,200+</div>
              <div className="stat-label">{t('heroStat1')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">98%</div>
              <div className="stat-label">{t('heroStat2')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">A1 - C1</div>
              <div className="stat-label">{t('heroStat3')}</div>
            </div>
          </div>
        </div>

        <div className="hero-image-wrapper">
          <div className="hero-image-container">
            <img 
              src="/images/hero_students.jpg" 
              alt="Academia Lumina Language Students" 
              className="hero-main-img"
              loading="lazy"
            />
            <div className="hero-floating-badge badge-top-right">
              <Award size={18} className="gold-icon" />
              <span>MCER / CEFR Certified</span>
            </div>
            <div className="hero-floating-badge badge-bottom-left">
              <CheckCircle2 size={18} className="gold-icon" />
              <span>Native Certified Faculty</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
