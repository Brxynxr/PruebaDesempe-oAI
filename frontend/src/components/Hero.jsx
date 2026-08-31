import React from 'react';

export default function Hero({ onOpenChat }) {
  return (
    <section className="hero" id="inicio">
      <h1>Domina Nuevos Idiomas con Academia Lumina</h1>
      <p>
        Aprende Inglés, Francés y Portugués en modalidad presencial o virtual.
        Niveles A1 a C1 con certificación oficial al finalizar cada semestre.
      </p>
      <button className="hero-cta" onClick={onOpenChat}>
        Consultar con Asistente Virtual 🤖
      </button>
    </section>
  );
}
