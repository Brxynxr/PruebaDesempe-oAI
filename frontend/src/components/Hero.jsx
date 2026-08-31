import React from 'react';
import { Sparkles, ArrowRight, Award, Users, CheckCircle2 } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function Hero({ onOpenChat }) {
  const { t } = useLanguage();

  return (
    <section className="hero-egyptian">
      <div className="hero-container">
        <div className="hero-content">
          <div className="egyptian-badge">
            <Sparkles size={14} className="badge-icon" />
            <span>{t('heroBadge')}</span>
          </div>
          
          <h1 className="hero-main-title">
            {t('heroTitle')}
          </h1>
          
          <p className="hero-main-desc">
            {t('heroSubtitle')}
          </p>

          <div className="hero-actions">
            <button className="btn-egyptian-gold" onClick={onOpenChat}>
              <span>{t('heroCtaChat')}</span>
              <ArrowRight size={18} />
            </button>
            <a href="#programas" className="btn-secondary">
              {t('heroCtaPrograms')}
            </a>
          </div>

          <div className="hero-features-chips">
            <div className="chip">
              <Users size={16} className="gold-icon" />
              <span>1,200+ {t('heroStat1')}</span>
            </div>
            <div className="chip">
              <CheckCircle2 size={16} className="gold-icon" />
              <span>98% {t('heroStat2')}</span>
            </div>
            <div className="chip">
              <Award size={16} className="gold-icon" />
              <span>A1 - C1 {t('heroStat3')}</span>
            </div>
          </div>
        </div>

        <div className="hero-image-wrapper">
          <div className="image-frame-gold">
            <img 
              src="/images/hero_students.jpg" 
              alt="Academia Lumina Language Students" 
              className="hero-students-img"
              loading="lazy"
            />
            <div className="image-overlay-badge">
              <Award size={16} className="gold-icon" />
              <span>CEFR / MCER Certified Faculty</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
