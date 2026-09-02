import React, { createContext, useContext, useState, useEffect } from 'react';

const translations = {
  en: {
    // Navbar
    homeAndPrograms: 'Home & Programs',
    modalitiesAndCert: 'Modalities & Certification',
    aiAssistant: 'AI Assistant',
    
    // Hero
    heroBadge: 'ACCREDITED LANGUAGE ACADEMY',
    heroTitle: 'Master English, French & Portuguese with AI Excellence',
    heroSubtitle: 'Certified CEFR methodology (A1 to C1), native teachers, in-person campus and live interactive virtual classes.',
    heroCtaChat: 'Chat with AI Assistant',
    heroCtaPrograms: 'Explore Programs',
    heroStat1: 'Active & Graduated Students',
    heroStat2: 'Official Pass Rate',
    heroStat3: 'CEFR Certification',
    heroRating: 'Verified Rating',
    heroStudentsBadge: 'Active & Graduated Students',

    // Why Us
    whyUsTitle: 'Why Choose Academia Lumina?',
    whyUsSubtitle: 'An academic ecosystem designed for rapid fluency and professional international certification.',
    benefit1Title: 'Live Interactive Classes',
    benefit1Desc: 'Small groups with native-level certified teachers in live dynamic sessions.',
    benefit1Detail: 'Maximum 15 students per classroom with constant speaking practice and individualized feedback.',
    benefit2Title: 'Official CEFR Certification',
    benefit2Desc: 'Structured progression from A1 (Beginner) to C1 (Effective Operational Proficiency).',
    benefit2Detail: 'Complies with the Common European Framework of Reference for Languages, valid for international visas and universities.',
    benefit3Title: '24/7 AI-Powered Support',
    benefit3Desc: 'Instant query resolution powered by intelligent RAG assistance and direct advisor escalation.',
    benefit3Detail: 'Instant answers for schedules, syllabus, and enrollment fees with direct WhatsApp advisor booking.',
    viewDetail: 'View details',
    hideDetail: 'Hide details',

    // Programs
    programsTitle: 'Our Academic Language Programs',
    programsSubtitle: 'Select a language to view methodology, pricing, schedules, and curriculum.',
    allLanguages: 'All Languages',
    english: 'English',
    french: 'French',
    portuguese: 'Portuguese',
    programEnglishDesc: 'General and Advanced English with focus on international certifications (TOEFL, IELTS, Cambridge).',
    programFrenchDesc: 'Intensive and Standard French oriented towards DELF/DALF certifications and study abroad.',
    programPortugueseDesc: 'Business and Conversational Portuguese for professional, travel, and international commerce.',
    inPersonPrice: 'In-Person',
    virtualPrice: 'Virtual Live',
    perSemester: '/ semester',
    features: 'Key Features',
    viewMethodology: 'View Methodology & Pricing',
    hideMethodology: 'Hide Details',
    inquireProgram: 'Ask AI about this program',

    // Modalities
    modalitiesTitle: 'Study Modalities',
    modalitiesSubtitle: 'Choose the format that best fits your lifestyle and learning routine.',
    inPersonTitle: 'In-Person Campus Modality',
    inPersonDesc: 'Interactive classrooms in our main Colombia headquarters with immersive language labs.',
    virtualTitle: 'Virtual Interactive Modality',
    virtualDesc: 'Live online classes with recorded sessions available for 30 days and 24/7 cloud platform access.',
    schedulesMorning: 'Morning Schedule (Mon - Thu: 7:00 AM - 9:00 AM)',
    schedulesEvening: 'Evening Schedule (Mon - Thu: 6:30 PM - 8:30 PM)',
    schedulesSaturday: 'Saturday Intensive (8:00 AM - 1:00 PM)',
    intensity: 'Intensity',
    hoursPerWeek: '8 to 10 hours / week',
    viewSchedules: 'View Schedules & Requirements',
    hideSchedules: 'Hide Details',

    // How It Works & Flowchart
    howItWorksTitle: 'How Your Learning Works',
    howItWorksSubtitle: 'A clear, structured path from your initial placement test to advanced international accreditation.',
    step1Title: '1. Online Registration',
    step1Desc: 'Fill your profile on our website and select your target language.',
    step2Title: '2. Placement Test',
    step2Desc: 'Assess your starting CEFR level (A1 to C1) with our online evaluation.',
    step3Title: '3. Immersive Learning',
    step3Desc: 'Attend live classes, practice speaking, and access digital PDF materials.',
    step4Title: '4. Official Certificate',
    step4Desc: 'Complete 80% attendance, pass final exams, and receive your diploma.',
    interactivePathTitle: 'Interactive CEFR Progression Path (A1 → C1)',
    interactivePathDesc: 'Click on each milestone node below to inspect academic competencies and learning goals.',

    // Certification
    certTitle: 'Official CEFR International Certification',
    certSubtitle: 'Your diploma is backed by European standards and recognized by universities and multinational corporations.',
    certRequirement1: 'Minimum 80% attendance to live or in-person sessions.',
    certRequirement2: 'Passing score of 75% or higher on end-of-level evaluations.',
    certRequirement3: 'Official digital and physical certificate with verifiable QR verification code.',

    // Testimonials
    testimonialsTitle: 'Student Success Stories',
    testimonialsSubtitle: 'Discover how Academia Lumina has transformed professional careers and language skills.',
    testimonial1Role: 'Software Engineer • Advanced English C1',
    testimonial1Comment: 'Thanks to Academia Lumina, I certified my C1 English level and was hired by an international tech company working remotely.',
    testimonial2Role: 'International Relations • Intensive French B2',
    testimonial2Comment: 'The interactive live methodology and native teachers made passing the DELF B2 exam a clear and rewarding experience.',
    testimonial3Role: 'Foreign Trade Director • Business Portuguese B1',
    testimonial3Comment: 'Focusing on business negotiation and accent coaching allowed me to close key partnerships in São Paulo with full confidence.',

    // Footer
    footerDesc: 'Leading language academy in Colombia. Excellence in English, French, and Portuguese education.',
    footerRights: 'All rights reserved.',

    // Chat
    chatHeader: 'Academia Lumina - AI Assistant',
    chatPlaceholder: 'Type your question here...',
    chatTyping: 'Assistant is typing...',
    chatInitialGreeting: 'Hi! I\'m Academia Lumina\'s virtual assistant. How can I help you today? You can ask me about pricing, schedules, English, French, or Portuguese levels, and enrollment.',
    chatInactivity: 'Do you have any other questions I can help you with?',
    chatLeadTitle: 'Connect with a Personal Advisor',
    chatFullName: 'Your Full Name:',
    chatPhone: 'WhatsApp / Phone Number:',
    chatSubmitLead: 'Request Direct Contact',
    chatLeadSuccess: 'Great {name}! Your contact details have been sent to our admissions team. We will contact you shortly on WhatsApp (+57 {phone}).',
    chatAdvisorPrompt: 'Would you like us to connect you with an admissions advisor to resolve your personalized inquiry?',
    chatAdvisorYes: 'Yes, connect with advisor',
    chatAdvisorNo: 'No, thanks',
    chatAdvisorDeclined: 'Understood! If you have any other questions or inquiries about our programs, I will be glad to help you. 😊'
  },

  es: {
    // Navbar
    homeAndPrograms: 'Inicio & Programas',
    modalitiesAndCert: 'Modalidades & Certificación',
    aiAssistant: 'Asistente IA',
    
    // Hero
    heroBadge: 'ACADEMIA DE IDIOMAS ACREDITADA',
    heroTitle: 'Domina Inglés, Francés y Portugués con Inteligencia y Excelencia',
    heroSubtitle: 'Metodología certificada MCER (A1 a C1), docentes nativos, sede presencial y clases virtuales interactivas en vivo.',
    heroCtaChat: 'Consultar Asistente IA',
    heroCtaPrograms: 'Explorar Programas',
    heroStat1: 'Estudiantes Activos y Graduados',
    heroStat2: 'Tasa de Aprobación',
    heroStat3: 'Certificación MCER',
    heroRating: 'Calificación Verificada',
    heroStudentsBadge: 'Estudiantes Graduados y Activos',

    // Why Us
    whyUsTitle: '¿Por qué elegir Academia Lumina?',
    whyUsSubtitle: 'Un ecosistema académico diseñado para lograr fluidez rápida y certificación internacional oficial.',
    benefit1Title: 'Clases Interactivas en Vivo',
    benefit1Desc: 'Grupos reducidos con docentes certificados en sesiones dinámicas y participativas.',
    benefit1Detail: 'Máximo 15 estudiantes por aula para garantizar práctica conversacional continua y retroalimentación personalizada.',
    benefit2Title: 'Certificación Oficial MCER',
    benefit2Desc: 'Estructura progresiva desde A1 (Principiante) hasta C1 (Dominio Operativo Eficaz).',
    benefit2Detail: 'Alineado con el Marco Común Europeo de Referencia para las Lenguas, válido para visas y universidades internacionales.',
    benefit3Title: 'Atención Inteligente 24/7',
    benefit3Desc: 'Resolución instantánea de dudas con IA RAG y escalamiento directo con asesores.',
    benefit3Detail: 'Respuestas al instante sobre horarios, programas y costos, con opción de agendamiento directo a WhatsApp.',
    viewDetail: 'Ver detalle',
    hideDetail: 'Ocultar detalle',

    // Programs
    programsTitle: 'Nuestros Programas de Idiomas',
    programsSubtitle: 'Selecciona un idioma para consultar metodología, precios, horarios y plan de estudios.',
    allLanguages: 'Todos los Idiomas',
    english: 'Inglés',
    french: 'Francés',
    portuguese: 'Portugués',
    programEnglishDesc: 'Inglés General y Avanzado enfocado en certificaciones internacionales (TOEFL, IELTS, Cambridge).',
    programFrenchDesc: 'Francés Intensivo y Estándar orientado a exámenes oficiales DELF/DALF y estudios en el exterior.',
    programPortugueseDesc: 'Portugués de Negocios y Conversacional para desarrollo profesional y comercio internacional.',
    inPersonPrice: 'Presencial',
    virtualPrice: 'Virtual en Vivo',
    perSemester: '/ semestre',
    features: 'Características Principales',
    viewMethodology: 'Ver Metodología y Precios',
    hideMethodology: 'Ocultar Detalles',
    inquireProgram: 'Consultar este programa en el Chat',

    // Modalities
    modalitiesTitle: 'Modalidades de Estudio',
    modalitiesSubtitle: 'Elige el formato que mejor se adapte a tu horario y ritmo de vida.',
    inPersonTitle: 'Modalidad Presencial en Sede',
    inPersonDesc: 'Aulas interactivas en nuestra sede principal de Colombia con laboratorios de inmersión lingüística.',
    virtualTitle: 'Modalidad Virtual Interactiva',
    virtualDesc: 'Clases en vivo con grabaciones disponibles por 30 días y acceso a la plataforma digital 24/7.',
    schedulesMorning: 'Horario Mañana (Lun - Jue: 7:00 AM - 9:00 AM)',
    schedulesEvening: 'Horario Noche (Lun - Jue: 6:30 PM - 8:30 PM)',
    schedulesSaturday: 'Sábados Intensivo (8:00 AM - 1:00 PM)',
    intensity: 'Intensidad',
    hoursPerWeek: '8 a 10 horas / semana',
    viewSchedules: 'Ver Horarios y Requisitos',
    hideSchedules: 'Ocultar Detalles',

    // How It Works & Flowchart
    howItWorksTitle: '¿Cómo Funciona tu Aprendizaje?',
    howItWorksSubtitle: 'Una ruta estructurada desde tu registro inicial hasta la certificación internacional avanzada.',
    step1Title: '1. Inscripción en Línea',
    step1Desc: 'Registra tus datos en nuestro portal web y selecciona tu idioma de interés.',
    step2Title: '2. Prueba de Nivelación',
    step2Desc: 'Evalúa tu nivel MCER de partida (A1 a C1) con nuestro examen diagnóstico.',
    step3Title: '3. Clases de Inmersión',
    step3Desc: 'Participa en sesiones dinámicas y accede al material académico digital.',
    step4Title: '4. Certificación Oficial',
    step4Desc: 'Cumple el 80% de asistencia, aprueba los exámenes y recibe tu diploma.',
    interactivePathTitle: 'Ruta de Aprendizaje Interactiva MCER (A1 → C1)',
    interactivePathDesc: 'Haz clic en cada nivel para conocer las competencias comunicativas y objetivos de aprendizaje.',

    // Certification
    certTitle: 'Certificación Internacional Oficial MCER',
    certSubtitle: 'Tu diploma cuenta con respaldo según estándares europeos y es válido para empresas y universidades.',
    certRequirement1: 'Mínimo del 80% de asistencia a clases programadas.',
    certRequirement2: 'Calificación aprobatoria igual o superior al 75% en evaluaciones.',
    certRequirement3: 'Diploma físico y digital con código QR de verificación de autenticidad.',

    // Testimonials
    testimonialsTitle: 'Testimonios de Estudiantes',
    testimonialsSubtitle: 'Conoce cómo Academia Lumina ha impulsado el crecimiento profesional de nuestros egresados.',
    testimonial1Role: 'Ingeniera de Software • Inglés Avanzado C1',
    testimonial1Comment: 'Gracias a Academia Lumina logré certificar mi nivel C1 de inglés y fui contratada por una empresa internacional en modalidad remota.',
    testimonial2Role: 'Relaciones Internacionales • Francés B2',
    testimonial2Comment: 'La metodología interactiva y los docentes nativos hicieron que pasar el examen DELF B2 fuera una experiencia clara y estructurada.',
    testimonial3Role: 'Directora de Comercio Exterior • Portugués B1',
    testimonial3Comment: 'El enfoque en negociación y pronunciación me permitió cerrar alianzas comerciales directas en São Paulo con total seguridad.',

    // Footer
    footerDesc: 'Academia líder de idiomas en Colombia. Excelencia en la enseñanza de Inglés, Francés y Portugués.',
    footerRights: 'Todos los derechos reservados.',

    // Chat
    chatHeader: 'Academia Lumina - Asistente IA',
    chatPlaceholder: 'Escribe tu consulta aquí...',
    chatTyping: 'El asistente está escribiendo...',
    chatInitialGreeting: '¡Hola! Soy el asistente virtual de Academia Lumina. ¿En qué te puedo colaborar hoy? Puedes preguntarme sobre precios, horarios, niveles de inglés, francés o portugués e inscripciones.',
    chatInactivity: '¿Tienes alguna otra duda o consulta en la que te pueda colaborar?',
    chatLeadTitle: 'Conectar con un Asesor Personalizado',
    chatFullName: 'Tu Nombre Completo:',
    chatPhone: 'Número de WhatsApp / Teléfono:',
    chatProgram: 'Programa de Interés:',
    chatSubmitLead: 'Solicitar Contacto Directo',
    chatLeadSuccess: '¡Excelente {name}! Tus datos fueron enviados a nuestro equipo de admisiones. Te contactaremos en breve por WhatsApp (+57 {phone}).',
    chatAdvisorPrompt: '¿Deseas que te comuniquemos con un asesor de admisiones para resolver tu consulta personalizada?',
    chatAdvisorYes: 'Sí, conectar con asesor',
    chatAdvisorNo: 'No, gracias',
    chatAdvisorDeclined: '¡De acuerdo! Si tienes alguna otra duda o consulta sobre nuestros programas, con mucho gusto aquí estaré para colaborarte. 😊'
  }
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('lumina_lang') || 'en';
  });

  const toggleLanguage = () => {
    setLanguage((prev) => {
      const next = prev === 'en' ? 'es' : 'en';
      localStorage.setItem('lumina_lang', next);
      return next;
    });
  };

  const t = (key, params = {}) => {
    let text = translations[language]?.[key] || translations['en']?.[key] || key;
    Object.keys(params).forEach((paramKey) => {
      text = text.replace(`{${paramKey}}`, params[paramKey]);
    });
    return text;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
