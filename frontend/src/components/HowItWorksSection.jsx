import React from 'react';
import { UserCheck, FileText, BookOpen, Award } from 'lucide-react';
import InteractiveFlowchart from './InteractiveFlowchart';
import { useLanguage } from '../context/LanguageContext';

export default function HowItWorksSection() {
  const { t } = useLanguage();

  const steps = [
    {
      number: '01',
      icon: <UserCheck size={24} />,
      title: t('step1Title'),
      desc: t('step1Desc')
    },
    {
      number: '02',
      icon: <FileText size={24} />,
      title: t('step2Title'),
      desc: t('step2Desc')
    },
    {
      number: '03',
      icon: <BookOpen size={24} />,
      title: t('step3Title'),
      desc: t('step3Desc')
    },
    {
      number: '04',
      icon: <Award size={24} />,
      title: t('step4Title'),
      desc: t('step4Desc')
    }
  ];

  return (
    <section id="metodologia" className="section-container how-it-works-section">
      <div className="section-header text-center">
        <h2 className="section-title">{t('howItWorksTitle')}</h2>
        <p className="section-subtitle">
          {t('howItWorksSubtitle')}
        </p>
      </div>

      <div className="steps-container">
        {steps.map((s, idx) => (
          <div key={idx} className="step-card">
            <div className="step-badge">{s.number}</div>
            <div className="step-icon-box">
              {s.icon}
            </div>
            <h3 className="step-title">{s.title}</h3>
            <p className="step-desc">{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Interactive CEFR Progression Flowchart */}
      <InteractiveFlowchart />
    </section>
  );
}
