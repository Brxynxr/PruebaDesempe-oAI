import React from 'react';

const programs = [
  {
    title: 'Programa de Inglés',
    description: 'Niveles A1 a C1. Enfoque conversacional y profesional.',
    presencial: '$450.000 COP / semestre',
    virtual: '$380.000 COP / semestre'
  },
  {
    title: 'Programa de Francés',
    description: 'Niveles A1 a C1. Aprendizaje dinámico y preparación oficial.',
    presencial: '$450.000 COP / semestre',
    virtual: '$380.000 COP / semestre'
  },
  {
    title: 'Programa de Portugués',
    description: 'Niveles A1 a C1. Ideal para negocios y viajes internacionales.',
    presencial: '$450.000 COP / semestre',
    virtual: '$380.000 COP / semestre'
  }
];

export default function ProgramsSection() {
  return (
    <section className="programs-container" id="programas">
      <h2 className="section-title">Nuestros Programas de Idiomas</h2>
      <div className="cards-grid">
        {programs.map((prog, idx) => (
          <div key={idx} className="card">
            <h3 className="card-title">{prog.title}</h3>
            <p>{prog.description}</p>
            <div className="price-tag">Presencial: {prog.presencial}</div>
            <div className="price-tag">Virtual: {prog.virtual}</div>
            <p className="price-detail">Inscripciones abiertas en Enero y Julio</p>
          </div>
        ))}
      </div>
    </section>
  );
}
