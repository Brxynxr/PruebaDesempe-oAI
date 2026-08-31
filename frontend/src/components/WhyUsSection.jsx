import React, { useState } from 'react';
import { Users, Award, Bot, ChevronDown, ChevronUp } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function WhyUsSection() {
  const { t } = useLanguage();
  const [expandedCards, setExpandedCards] = useState({});

  const toggleCard = (index) => {
    setExpandedCards((prev) => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const benefits = [
    {
      icon: <Users size={28} />,
      title: t('benefit1Title'),
      desc: t('benefit1Desc'),
      detail: t('benefit1Detail')
    },
    {
      icon: <Award size={28} />,
      title: t('benefit2Title'),
      desc: t('benefit2Desc'),
      detail: t('benefit2Detail')
    },
    {
      icon: <Bot size={28} />,
      title: t('benefit3Title'),
      desc: t('benefit3Desc'),
      detail: t('benefit3Detail')
    }
  ];

  return (
    <section className="section-container why-us-section">
      <div className="section-header text-center">
        <h2 className="section-title">{t('whyUsTitle')}</h2>
        <p className="section-subtitle">
          {t('whyUsSubtitle')}
        </p>
      </div>

      <div className="benefits-grid">
        {benefits.map((b, idx) => {
          const isExpanded = !!expandedCards[idx];
          return (
            <div 
              key={idx} 
              className={`benefit-card ${isExpanded ? 'expanded' : ''}`}
              onClick={() => toggleCard(idx)}
              style={{ cursor: 'pointer' }}
            >
              <div className="benefit-icon-wrapper">
                {b.icon}
              </div>
              <h3 className="benefit-title">{b.title}</h3>
              <p className="benefit-desc">{b.desc}</p>
              
              <button 
                className="btn-expand-toggle-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleCard(idx);
                }}
              >
                <span>{isExpanded ? t('hideDetail') : t('viewDetail')}</span>
                {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              {isExpanded && (
                <div className="benefit-detail-drawer fade-in">
                  <p>{b.detail}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
