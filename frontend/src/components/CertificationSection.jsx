import React from 'react';
import { Award, CheckCircle, ShieldCheck, FileCheck2 } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function CertificationSection() {
  const { t } = useLanguage();

  return (
    <section id="certificacion" className="section-container certification-section">
      <div className="certification-card">
        <div className="certification-content">
          <div className="cert-badge">
            <Award size={16} />
            <span>CEFR / MCER Standard</span>
          </div>

          <h2 className="cert-title">{t('certTitle')}</h2>
          <p className="cert-desc">
            {t('certSubtitle')}
          </p>

          <div className="cert-requirements-list">
            <div className="cert-req-item">
              <CheckCircle size={18} className="gold-icon" />
              <span>{t('certRequirement1')}</span>
            </div>
            <div className="cert-req-item">
              <CheckCircle size={18} className="gold-icon" />
              <span>{t('certRequirement2')}</span>
            </div>
            <div className="cert-req-item">
              <CheckCircle size={18} className="gold-icon" />
              <span>{t('certRequirement3')}</span>
            </div>
          </div>
        </div>

        <div className="certification-visual">
          <div className="diploma-mockup">
            <div className="diploma-header">
              <ShieldCheck size={36} className="gold-icon" />
              <span>ACADEMIA LUMINA</span>
            </div>
            <div className="diploma-body">
              <div className="diploma-line large"></div>
              <div className="diploma-line medium"></div>
              <div className="diploma-seal">
                <FileCheck2 size={24} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
