import React, { useState } from 'react';
import { ChevronDown, HelpCircle } from 'lucide-react';

const faqs = [
  {
    question: '¿Cuáles son los precios y métodos de pago disponibles?',
    answer: 'El costo por semestre (16 semanas) es de $450.000 COP para modalidad presencial y $380.000 COP para modalidad virtual. Aceptamos transferencias bancarias, tarjetas de crédito/débito y pagos 100% en línea.'
  },
  {
    question: '¿Qué horarios y frecuencias puedo elegir?',
    answer: 'En modalidad presencial ofrecemos clases entre semana (Mañana: 8:00 - 10:00 AM | Noche: 6:30 - 8:30 PM). En modalidad virtual ofrecemos clases en vivo entre semana y la opción de Sábados Intensivos de 8:00 AM a 1:00 PM.'
  },
  {
    question: '¿Qué niveles puedo certificar y con qué estándar?',
    answer: 'Puedes certificar desde el nivel Principiante (A1) hasta Avanzado (C1). Todas nuestras certificaciones se rigen bajo los parámetros del Marco Común Europeo de Referencia para las Lenguas (MCER).'
  },
  {
    question: '¿Cuál es la diferencia entre la modalidad Presencial y Virtual?',
    answer: 'En la modalidad presencial asistes a nuestra sede principal en Colombia en aulas de máximo 15 estudiantes. En la modalidad virtual te conectas en vivo mediante plataforma digital y tienes acceso a las grabaciones durante 30 días.'
  },
  {
    question: '¿Cómo funciona la prueba de nivelación y tiene algún costo?',
    answer: 'La prueba de diagnóstico de nivelación se realiza totalmente en línea de forma rápida y no tiene ningún costo. Te permite ingresar al nivel exacto que corresponde a tus competencias actuales.'
  },
  {
    question: '¿Cuándo se abren las inscripciones?',
    answer: 'Las inscripciones se habilitan dos veces al año: para el primer semestre abren del 1 de noviembre al 20 de enero (clases inician en febrero), y para el segundo semestre del 1 de mayo al 20 de julio (clases inician en agosto).'
  }
];

export default function FaqSection() {
  const [openIndex, setOpenIndex] = useState(null);

  const toggleFaq = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="section-container" id="faq">
      <div className="section-header">
        <span className="section-subtitle">Resolvemos tus dudas</span>
        <h2 className="section-title">Preguntas Frecuentes</h2>
        <p className="section-description">
          Todo lo que necesitas saber antes de iniciar tu proceso de inscripción en Academia Lumina.
        </p>
      </div>

      <div className="faq-container">
        {faqs.map((item, idx) => (
          <div
            key={idx}
            className={`faq-item ${openIndex === idx ? 'faq-open' : ''}`}
            onClick={() => toggleFaq(idx)}
          >
            <div className="faq-question">
              <div className="faq-q-text">
                <HelpCircle size={20} className="faq-icon" />
                <span>{item.question}</span>
              </div>
              <ChevronDown size={20} className="faq-arrow" />
            </div>

            {openIndex === idx && (
              <div className="faq-answer">
                <p>{item.answer}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
