import React from 'react';
import { Sparkles, ArrowRight, Award, Users, CheckCircle2, Star, GraduationCap } from 'lucide-react';
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
              <span>+12.000+ {t('heroStat1')}</span>
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

        {/* Hero Image Showcase intertwined with floating glassmorphic badges */}
        <div className="hero-image-wrapper">
          <div className="hero-ambient-glow"></div>
          <div className="image-frame-gold">
            <img 
              src="/images/hero_students.jpg" 
              alt="Academia Lumina Language Students" 
              className="hero-students-img"
              loading="lazy"
            />
            
            {/* Subtle Gradient Blend Overlay */}
            <div className="image-blend-gradient"></div>

            {/* Top Rating Badge */}
            <div className="floating-hero-pill top-right-pill">
              <Star size={14} fill="#f5cd47" color="#f5cd47" />
              <span>4.9/5 {t('heroRating')}</span>
            </div>

            {/* Bottom Intertwined Students Stat Badge */}
            <div className="floating-hero-card bottom-card">
              <div className="floating-card-icon">
                <GraduationCap size={22} />
              </div>
              <div className="floating-card-info">
                <div className="floating-card-num">+12.000+</div>
                <div className="floating-card-text">{t('heroStudentsBadge')}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
