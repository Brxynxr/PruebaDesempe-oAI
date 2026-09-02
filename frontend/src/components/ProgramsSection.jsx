import React, { useState } from 'react';
import { BookOpen, Check, Sparkles, ChevronDown, ChevronUp, Layers, Globe } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function ProgramsSection({ onOpenChat }) {
  const { t } = useLanguage();
  const [activeFilter, setActiveFilter] = useState('all');
  const [expandedCards, setExpandedCards] = useState({});

  const toggleCard = (id) => {
    setExpandedCards((prev) => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const programs = [
    {
      id: 'ingles',
      name: t('english'),
      flag: '🇬🇧',
      level: 'A1 - C1',
      badge: 'Popular',
      image: '/images/english_course.jpg',
      pricePresencial: '$450.000 COP',
      priceVirtual: '$380.000 COP',
      desc: t('programEnglishDesc'),
      methodology: 'Communicative task-based learning with focus on TOEFL, IELTS, and Cambridge certifications.',
      features: [
        'Interactive conversation workshops',
        'International exam simulations',
        'PDF materials and cloud grammar platform',
        'Academic writing and presentation labs'
      ]
    },
    {
      id: 'frances',
      name: t('french'),
      flag: '🇫🇷',
      level: 'A1 - B2',
      badge: 'DELF / DALF',
      image: '/images/french_course.jpg',
      pricePresencial: '$480.000 COP',
      priceVirtual: '$400.000 COP',
      desc: t('programFrenchDesc'),
      methodology: 'Action-oriented approach with focus on European academic exchange and DELF accreditation.',
      features: [
        'Phonetics and pronunciation lab',
        'Cultural cinema and conversation clubs',
        'Official DELF/DALF mock tests',
        'Native certified instructors'
      ]
    },
    {
      id: 'portugues',
      name: t('portuguese'),
      flag: '🇧🇷',
      level: 'A1 - B2',
      badge: 'Celpe-Bras',
      image: '/images/portuguese_course.jpg',
      pricePresencial: '$420.000 COP',
      priceVirtual: '$350.000 COP',
      desc: t('programPortugueseDesc'),
      methodology: 'Accelerated immersion for Spanish speakers targeting business, commerce, and Celpe-Bras certification.',
      features: [
        'Fast-track contrastive grammar for Hispanophones',
        'Business negotiations and vocabulary',
        'Celpe-Bras preparation workshops',
        'Live cultural immersion events'
      ]
    }
  ];

  const filteredPrograms = activeFilter === 'all' 
    ? programs 
    : programs.filter((p) => p.id === activeFilter);

  return (
    <section id="programas" className="section-container programs-section fade-in-section">
      <div className="section-header text-center">
        <h2 className="section-title">{t('programsTitle')}</h2>
        <p className="section-subtitle">
          {t('programsSubtitle')}
        </p>

        {/* Filter Tabs */}
        <div className="filter-bar">
          <button 
            className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`}
            onClick={() => setActiveFilter('all')}
          >
            <Globe size={16} />
            <span>{t('allLanguages')}</span>
          </button>
          <button 
            className={`filter-btn ${activeFilter === 'ingles' ? 'active' : ''}`}
            onClick={() => setActiveFilter('ingles')}
          >
            <span className="pill-flag">🇬🇧</span>
            <span>{t('english')}</span>
          </button>
          <button 
            className={`filter-btn ${activeFilter === 'frances' ? 'active' : ''}`}
            onClick={() => setActiveFilter('frances')}
          >
            <span className="pill-flag">🇫🇷</span>
            <span>{t('french')}</span>
          </button>
          <button 
            className={`filter-btn ${activeFilter === 'portugues' ? 'active' : ''}`}
            onClick={() => setActiveFilter('portugues')}
          >
            <span className="pill-flag">🇧🇷</span>
            <span>{t('portuguese')}</span>
          </button>
        </div>
      </div>

      <div className={`programs-grid ${filteredPrograms.length === 1 ? 'single-item' : ''}`}>
        {filteredPrograms.map((prog) => {
          const isExpanded = !!expandedCards[prog.id];
          return (
            <div key={prog.id} className={`program-card ${isExpanded ? 'expanded' : ''}`}>
              <div className="program-image-header">
                <img 
                  src={prog.image} 
                  alt={prog.name} 
                  className="program-banner-img"
                  loading="lazy"
                />
                <div className="program-image-overlay">
                  <span className="program-flag">{prog.flag}</span>
                  <span className="program-badge-tag">{prog.badge}</span>
                </div>
              </div>

              <div className="program-body">
                <div className="program-header">
                  <h3 className="program-name">{prog.name}</h3>
                  <span className="program-level-pill">{prog.level}</span>
                </div>

                <p className="program-desc">{prog.desc}</p>

                {/* Collapsible Accordion Drawer */}
                <button 
                  className="btn-expand-toggle"
                  onClick={() => toggleCard(prog.id)}
                  aria-expanded={isExpanded}
                >
                  <span>{isExpanded ? t('hideMethodology') : t('viewMethodology')}</span>
                  {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {isExpanded && (
                  <div className="expandable-content fade-in">
                    <div className="program-pricing-box">
                      <div className="pricing-col">
                        <span className="price-type">{t('inPersonPrice')}</span>
                        <div className="price-val">{prog.pricePresencial}</div>
                        <span className="price-sub">{t('perSemester')}</span>
                      </div>
                      <div className="pricing-col-divider"></div>
                      <div className="pricing-col">
                        <span className="price-type">{t('virtualPrice')}</span>
                        <div className="price-val">{prog.priceVirtual}</div>
                        <span className="price-sub">{t('perSemester')}</span>
                      </div>
                    </div>

                    <div className="methodology-box">
                      <strong><Layers size={14} /> Methodology:</strong>
                      <p>{prog.methodology}</p>
                    </div>

                    <div className="program-features-list">
                      <div className="features-title">{t('features')}</div>
                      {prog.features.map((feat, fidx) => (
                        <div key={fidx} className="feature-item">
                          <Check size={14} className="feature-check-icon" />
                          <span>{feat}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="program-footer">
                  <button className="btn-program-inquire" onClick={onOpenChat}>
                    <Sparkles size={14} />
                    <span>{t('inquireProgram')}</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
