import React, { useState } from 'react';
import { MapPin, Globe, Clock, Users, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function ModalitiesSection() {
  const { t } = useLanguage();
  const [expandedCards, setExpandedCards] = useState({});

  const toggleCard = (id) => {
    setExpandedCards((prev) => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  return (
    <section id="modalidades" className="modalities-section">
      <div className="section-header text-center">
        <h2 className="section-title">{t('modalitiesTitle')}</h2>
        <p className="section-subtitle">
          {t('modalitiesSubtitle')}
        </p>
      </div>

      <div className="modalities-grid">
        {/* Modality 1: In-Person */}
        <div className={`modality-card ${expandedCards['presencial'] ? 'expanded' : ''}`}>
          <div className="modality-icon-header">
            <div className="modality-icon presencial-icon">
              <MapPin size={24} />
            </div>
            <span className="modality-badge">Sede Colombia</span>
          </div>

          <h3 className="modality-title">{t('inPersonTitle')}</h3>
          <p className="modality-desc">
            {t('inPersonDesc')}
          </p>

          <button 
            className="btn-expand-toggle"
            onClick={() => toggleCard('presencial')}
          >
            <span>{expandedCards['presencial'] ? t('hideSchedules') : t('viewSchedules')}</span>
            {expandedCards['presencial'] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {expandedCards['presencial'] && (
            <div className="expandable-content fade-in">
              <div className="modality-details-list">
                <div className="modality-detail-item">
                  <Clock size={16} className="gold-icon" />
                  <span>{t('schedulesMorning')}</span>
                </div>
                <div className="modality-detail-item">
                  <Clock size={16} className="gold-icon" />
                  <span>{t('schedulesEvening')}</span>
                </div>
                <div className="modality-detail-item">
                  <Clock size={16} className="gold-icon" />
                  <span>{t('schedulesSaturday')}</span>
                </div>
                <div className="modality-detail-item">
                  <Users size={16} className="gold-icon" />
                  <span>Max 15 students per classroom</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modality 2: Virtual */}
        <div className={`modality-card ${expandedCards['virtual'] ? 'expanded' : ''}`}>
          <div className="modality-icon-header">
            <div className="modality-icon virtual-icon">
              <Globe size={24} />
            </div>
            <span className="modality-badge">100% Live Online</span>
          </div>

          <h3 className="modality-title">{t('virtualTitle')}</h3>
          <p className="modality-desc">
            {t('virtualDesc')}
          </p>

          <button 
            className="btn-expand-toggle"
            onClick={() => toggleCard('virtual')}
          >
            <span>{expandedCards['virtual'] ? t('hideSchedules') : t('viewSchedules')}</span>
            {expandedCards['virtual'] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {expandedCards['virtual'] && (
            <div className="expandable-content fade-in">
              <div className="modality-details-list">
                <div className="modality-detail-item">
                  <Clock size={16} className="gold-icon" />
                  <span>{t('schedulesMorning')}</span>
                </div>
                <div className="modality-detail-item">
                  <Clock size={16} className="gold-icon" />
                  <span>{t('schedulesEvening')}</span>
                </div>
                <div className="modality-detail-item">
                  <Clock size={16} className="gold-icon" />
                  <span>{t('schedulesSaturday')}</span>
                </div>
                <div className="modality-detail-item">
                  <Sparkles size={16} className="gold-icon" />
                  <span>Recordings available for 30 days</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
