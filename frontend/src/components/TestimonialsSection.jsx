import React from 'react';
import { Star, Quote } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function TestimonialsSection() {
  const { t } = useLanguage();

  const testimonials = [
    {
      name: 'Camila Restrepo',
      role: 'Ingeniera de Software',
      program: 'Inglés Avanzado B2 - C1',
      rating: 5,
      comment: 'Gracias a Academia Lumina logré certificar mi nivel C1 de inglés y fui contratada por una empresa internacional en modalidad remota.'
    },
    {
      name: 'Sebastián Mora',
      role: 'Estudiante de Relaciones Internacionales',
      program: 'Francés Intensivo DELF B2',
      rating: 5,
      comment: 'La metodología interactiva y los docentes nativos hicieron que pasar el examen DELF B2 fuera una experiencia clara y estructurada.'
    },
    {
      name: 'Valeria Gómez',
      role: 'Directora de Comercio Exterior',
      program: 'Portugués de Negocios B1',
      rating: 5,
      comment: 'El enfoque en negociación y pronunciación me permitió cerrar alianzas comerciales directas en São Paulo con total seguridad.'
    }
  ];

  return (
    <section className="testimonials-section">
      <div className="section-header text-center">
        <h2 className="section-title">{t('testimonialsTitle')}</h2>
        <p className="section-subtitle">
          {t('testimonialsSubtitle')}
        </p>
      </div>

      <div className="testimonials-grid">
        {testimonials.map((tItem, idx) => (
          <div key={idx} className="testimonial-card">
            <div className="quote-icon-box">
              <Quote size={20} />
            </div>
            
            <div className="stars-row">
              {[...Array(tItem.rating)].map((_, i) => (
                <Star key={i} size={14} fill="#d4af37" color="#d4af37" />
              ))}
            </div>

            <p className="testimonial-text">"{tItem.comment}"</p>

            <div className="testimonial-author">
              <div className="author-avatar">{tItem.name[0]}</div>
              <div>
                <h4 className="author-name">{tItem.name}</h4>
                <span className="author-role">{tItem.role} • {tItem.program}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
