import React, { useState } from 'react';
import { ArrowRight, CheckCircle2, Award, Zap, Compass, Star } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function InteractiveFlowchart() {
  const { language, t } = useLanguage();
  const [selectedLevel, setSelectedLevel] = useState('A1');

  const levels = [
    {
      id: 'A1',
      title: 'A1 - Beginner',
      titleEs: 'A1 - Principiante',
      duration: '1 Semester (4 months)',
      durationEs: '1 Semestre (4 meses)',
      focus: 'Daily routines, introductions, basic questions and immediate survival vocabulary.',
      focusEs: 'Rutinas cotidianas, presentaciones, preguntas básicas y vocabulario de supervivencia.',
      milestone: 'Basic social interaction and elementary comprehension.',
      milestoneEs: 'Interacción social básica y comprensión auditiva elemental.'
    },
    {
      id: 'A2',
      title: 'A2 - Elementary',
      titleEs: 'A2 - Básico / Plataforma',
      duration: '1 Semester (4 months)',
      durationEs: '1 Semestre (4 meses)',
      focus: 'Past and future narrative, shopping, employment, and local geography.',
      focusEs: 'Narrativa en pasado y futuro, compras, empleo y entorno inmediato.',
      milestone: 'Short social exchanges and descriptive conversations.',
      milestoneEs: 'Intercambios sociales breves y conversaciones descriptivas.'
    },
    {
      id: 'B1',
      title: 'B1 - Intermediate',
      titleEs: 'B1 - Intermedio / Umbral',
      duration: '1 Semester (4 months)',
      durationEs: '1 Semestre (4 meses)',
      focus: 'Opinions, plans, experiences, travel situations, and coherent text production.',
      focusEs: 'Expresión de opiniones, planes, experiencias, viajes y redacción coherente.',
      milestone: 'Independence in standard communication situations.',
      milestoneEs: 'Independencia en situaciones cotidianas de viaje y trabajo.'
    },
    {
      id: 'B2',
      title: 'B2 - Upper Intermediate',
      titleEs: 'B2 - Avanzado / Competente',
      duration: '1 Semester (4 months)',
      durationEs: '1 Semestre (4 meses)',
      focus: 'Complex abstract texts, technical discussions, fluent spontaneous interaction with native speakers.',
      focusEs: 'Textos complejos y abstractos, debates técnicos y fluidez espontánea con nativos.',
      milestone: 'Professional and academic certification threshold (TOEFL / DELF).',
      milestoneEs: 'Umbral de certificación profesional y académica internacional.'
    },
    {
      id: 'C1',
      title: 'C1 - Effective Proficiency',
      titleEs: 'C1 - Dominio Operativo Eficaz',
      duration: '1 Semester (4 months)',
      durationEs: '1 Semestre (4 meses)',
      focus: 'Implicit meaning recognition, nuanced academic discourse, complex structured writing.',
      focusEs: 'Reconocimiento de sentido implícito, discurso académico flexible y redacción compleja.',
      milestone: 'Full bilingual mastery for leadership, academia, and international enterprise.',
      milestoneEs: 'Dominio bilingüe pleno para liderazgo, academia y negocios globales.'
    }
  ];

  const activeData = levels.find((l) => l.id === selectedLevel) || levels[0];

  return (
    <div className="flowchart-wrapper">
      <div className="flowchart-header">
        <Compass size={20} className="gold-icon" />
        <div>
          <h3 className="flowchart-title">{t('interactivePathTitle')}</h3>
          <p className="flowchart-subtitle">{t('interactivePathDesc')}</p>
        </div>
      </div>

      {/* Interactive Step Nodes Bar */}
      <div className="flowchart-nodes-bar">
        {levels.map((lvl, index) => {
          const isSelected = lvl.id === selectedLevel;
          return (
            <React.Fragment key={lvl.id}>
              <button
                className={`flowchart-node ${isSelected ? 'selected' : ''}`}
                onClick={() => setSelectedLevel(lvl.id)}
              >
                <span className="node-level-tag">{lvl.id}</span>
                <span className="node-level-name">{language === 'es' ? lvl.titleEs.split(' - ')[1] : lvl.title.split(' - ')[1]}</span>
              </button>

              {index < levels.length - 1 && (
                <div className="flowchart-arrow-connector">
                  <ArrowRight size={16} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Selected Level Detail Card */}
      <div className="flowchart-detail-box fade-in">
        <div className="detail-box-top">
          <div>
            <span className="detail-level-badge">{activeData.id}</span>
            <h4 className="detail-level-title">{language === 'es' ? activeData.titleEs : activeData.title}</h4>
          </div>
          <div className="detail-duration-tag">
            <Zap size={14} />
            <span>{language === 'es' ? activeData.durationEs : activeData.duration}</span>
          </div>
        </div>

        <div className="detail-grid">
          <div className="detail-col">
            <strong><CheckCircle2 size={16} className="gold-icon" /> {language === 'es' ? 'Enfoque Pedagógico:' : 'Pedagogical Focus:'}</strong>
            <p>{language === 'es' ? activeData.focusEs : activeData.focus}</p>
          </div>
          <div className="detail-col">
            <strong><Award size={16} className="gold-icon" /> {language === 'es' ? 'Hito y Certificación:' : 'Milestone & Certification:'}</strong>
            <p>{language === 'es' ? activeData.milestoneEs : activeData.milestone}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
