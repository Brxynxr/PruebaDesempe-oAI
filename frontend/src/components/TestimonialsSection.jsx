import React from 'react';
import { Star, Quote } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function TestimonialsSection() {
  const { t } = useLanguage();

  const testimonials = [
    {
      name: 'Camila Restrepo',
      role: t('testimonial1Role'),
      avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=200&auto=format&fit=crop&q=80',
      rating: 5,
      comment: t('testimonial1Comment')
    },
    {
      name: 'Sebastián Mora',
      role: t('testimonial2Role'),
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80',
      rating: 5,
      comment: t('testimonial2Comment')
    },
    {
      name: 'Valeria Gómez',
      role: t('testimonial3Role'),
      avatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=200&auto=format&fit=crop&q=80',
      rating: 5,
      comment: t('testimonial3Comment')
    }
  ];

  return (
    <section className="section-container testimonials-section">
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
              <Quote size={18} />
            </div>
            
            <div className="stars-row">
              {[...Array(tItem.rating)].map((_, i) => (
                <Star key={i} size={14} fill="#f5cd47" color="#f5cd47" />
              ))}
            </div>

            <p className="testimonial-text">"{tItem.comment}"</p>

            <div className="testimonial-author">
              <img 
                src={tItem.avatar} 
                alt={tItem.name} 
                className="author-avatar-img" 
                loading="lazy"
              />
              <div className="author-info">
                <h4 className="author-name">{tItem.name}</h4>
                <span className="author-role">{tItem.role}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
