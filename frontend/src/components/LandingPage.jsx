import React, { useState } from 'react';
import { ArrowRight, BookOpen, CheckCircle2, Headphones, MessageCircle, Sparkles, Users, Globe, Award, ChevronRight, School, GraduationCap } from 'lucide-react';
import campusHero from '../assets/campus-hero.jpg';
import classroomImg from '../assets/classroom.jpg';
import testimonialAvatar from '../assets/testimonial-avatar.jpg';

const programs = [
  // INGLÉS
  {
    id: "english-exec",
    language: "Inglés",
    level: "B2–C1",
    title: "Inglés Ejecutivo y Negocios",
    description: "Reuniones de alta dirección, negociación internacional y redacción profesional con retroalimentación semanal personalizada.",
    duration: "12 semanas",
    modality: "Presencial / Virtual",
    color: "gold",
    tag: "Alta Demanda",
    price: "$450.000 / $380.000 COP"
  },
  {
    id: "english-general",
    language: "Inglés",
    level: "A1–B2",
    title: "Inglés General Progresivo",
    description: "Metodología integral de inmersión por niveles MCER (A1 a B2), desarrollo de fluidez conversacional y comprensión auditiva.",
    duration: "1 semestre / nivel",
    modality: "Presencial / Virtual",
    color: "gold",
    tag: "Metodología MCER",
    price: "$450.000 / $380.000 COP"
  },
  {
    id: "english-ielts",
    language: "Inglés",
    level: "B2–C1",
    title: "Preparación TOEFL & IELTS",
    description: "Simulacros cronometrados reales, técnicas clave para exámenes internacionales y tutoría con examinadores certificados.",
    duration: "8 semanas",
    modality: "Virtual en vivo",
    color: "gold",
    tag: "Certificación Oficial",
    price: "$380.000 COP"
  },

  // FRANCÉS
  {
    id: "french-intensive",
    language: "Francés",
    level: "B1–C1",
    title: "Francés Intensivo y Diplomacia",
    description: "Inmersión conversacional con fonética aplicada y cultura para profesionales, diplomacia, viajes y posgrados.",
    duration: "10 semanas",
    modality: "Virtual en vivo",
    color: "rose",
    tag: "Grupos reducidos",
    price: "$380.000 COP"
  },
  {
    id: "french-standard",
    language: "Francés",
    level: "A1–B2",
    title: "Francés General y Conversación",
    description: "Dominio de la lengua francesa desde nivel cero con club de conversación semanal y gramática estructurada.",
    duration: "1 semestre / nivel",
    modality: "Presencial / Virtual",
    color: "rose",
    tag: "Desde nivel A1",
    price: "$450.000 / $380.000 COP"
  },
  {
    id: "french-delf",
    language: "Francés",
    level: "B1–C1",
    title: "Preparación Examen DELF / DALF",
    description: "Entrenamiento focalizado en comprensión y expresión oral y escrita para obtener el diploma oficial de Francia.",
    duration: "8 semanas",
    modality: "Presencial / Virtual",
    color: "rose",
    tag: "Validez Vitalicia",
    price: "$380.000 COP"
  },

  // PORTUGUÉS
  {
    id: "portuguese-spoken",
    language: "Portugués",
    level: "A1–B2",
    title: "Portugués Hablado y Conversación",
    description: "Fluidez práctica acelerada para desenvolverte con naturalidad en viajes, vida cotidiana y cultura luso-brasileña.",
    duration: "8 semanas",
    modality: "Presencial / Virtual",
    color: "brand",
    tag: "Resultados en 60 días",
    price: "$450.000 / $380.000 COP"
  },
  {
    id: "portuguese-business",
    language: "Portugués",
    level: "B1–C1",
    title: "Portugués de Negocios y Tech",
    description: "Terminología comercial, acuerdos corporativos y comunicación orientada al mercado de Brasil y LATAM.",
    duration: "1 semestre / nivel",
    modality: "Presencial / Virtual",
    color: "brand",
    tag: "Enfoque Comercial",
    price: "$450.000 / $380.000 COP"
  },
  {
    id: "portuguese-celpe",
    language: "Portugués",
    level: "B2–C1",
    title: "Preparación Certificación Celpe-Bras",
    description: "Módulos de simulación práctica de audio y redacción para aprobar el examen oficial del Ministerio de Educación de Brasil.",
    duration: "6 semanas",
    modality: "Virtual en vivo",
    color: "brand",
    tag: "Examen Oficial",
    price: "$380.000 COP"
  }
];

const steps = [
  {
    number: "01",
    title: "Diagnóstico de Nivel",
    description: "Evaluación interactiva y personalizada de tu nivel actual y objetivos en 15 minutos.",
  },
  {
    number: "02",
    title: "Plan Personalizado",
    description: "Tu asesor diseña la ruta académica, horarios flexibles y objetivos de certificación.",
  },
  {
    number: "03",
    title: "Inicio Guiado",
    description: "Primera sesión inmersiva y acompañamiento continuo por mentores desde el día uno.",
  },
  {
    number: "04",
    title: "Certificación Oficial",
    description: "Examen final evaluado por examinadores y diploma digital con verificación pública.",
  },
];

const benefits = [
  {
    icon: Users,
    title: "Mentoría humana dedicada",
    description: "Asesores nativos y bilingües certificados que acompañan tu progreso semana a semana.",
  },
  {
    icon: BookOpen,
    title: "Metodología MCER",
    description: "Plan de estudios estructurado y alineado con el Marco Común Europeo de Referencia.",
  },
  {
    icon: CheckCircle2,
    title: "Certificación reconocida",
    description: "Diploma digital con código criptográfico verificable para tu currículum y LinkedIn.",
  },
  {
    icon: Headphones,
    title: "Soporte híbrido 24/7",
    description: "Tutor inteligente con IA para práctica continua y escalación inmediata a asesores humanos.",
  },
];

export default function LandingPage({ onOpenChat, onNavigateAdmin }) {
  const [activeFilter, setActiveFilter] = useState("Todos");

  const filteredPrograms =
    activeFilter === "Todos"
      ? programs.filter((p) => ["english-exec", "french-intensive", "portuguese-spoken"].includes(p.id))
      : programs.filter((p) => p.language === activeFilter);

  return (
    <div className="relative min-h-screen w-full bg-cream font-sans text-ink antialiased selection:bg-brand/30">
      {/* Warm sunset editorial gradient background */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(135deg, #FFF6EC 0%, #FCE3D2 38%, #F7D2CB 66%, #EAD7E8 100%)",
          }}
        />
        <div className="absolute -top-40 -right-28 h-[560px] w-[560px] rounded-full bg-gold/40 blur-3xl" />
        <div className="absolute -bottom-52 -left-40 h-[520px] w-[520px] rounded-full bg-accent-rose/25 blur-3xl" />
      </div>

      {/* Header */}
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 animate-rise">
        <div className="flex items-center gap-3">
          <button
            onClick={onNavigateAdmin}
            title="Academia Lumina"
            className="grid size-10 place-items-center rounded-2xl bg-white/60 ring-1 ring-black/5 backdrop-blur-md shadow-sm transition hover:scale-105 hover:bg-white active:scale-95 cursor-pointer"
          >
            <span className="text-xl font-bold text-brand font-display">L</span>
          </button>
          <span className="text-base font-semibold tracking-tight font-display text-ink select-none">
            Academia Lumina
          </span>
        </div>

        <nav className="hidden items-center gap-8 text-sm font-medium text-ink/70 md:flex">
          <a href="#inicio" className="text-ink transition hover:text-brand">Inicio</a>
          <a href="#programas" className="transition hover:text-brand">Programas</a>
          <a href="#proceso" className="transition hover:text-brand">Proceso</a>
          <a href="#certificacion" className="transition hover:text-brand">Certificación</a>
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenChat}
            className="rounded-full bg-ink px-5 py-2 text-sm font-medium text-cream shadow-sm transition hover:bg-ink/90 hover:shadow cursor-pointer"
          >
            Solicitar admisión
          </button>
        </div>
      </header>

      <main id="inicio" className="mx-auto max-w-7xl px-6">
        {/* Hero Section */}
        <section className="grid grid-cols-12 gap-8 lg:gap-12 pb-8 pt-4 lg:pt-6 items-center">
          <div className="col-span-12 lg:col-span-7 flex flex-col justify-center animate-rise">
            <div className="mb-4 inline-flex w-fit items-center gap-2 rounded-full bg-white/60 px-3.5 py-1.5 text-xs font-medium ring-1 ring-black/5 backdrop-blur-md">
              <span className="size-2 rounded-full bg-accent-rose animate-pulse" />
              <span className="text-ink/80">Admisiones abiertas · Convocatoria 2026</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-[3.5rem] font-light leading-[1.12] tracking-tight font-display text-ink">
              Aprende el idioma con{" "}
              <span className="italic text-brand font-normal">precisión</span> y confianza.
            </h1>

            <p className="mt-5 max-w-xl text-base leading-relaxed text-ink/75">
              Inglés, francés y portugués en programas personalizados guiados por asesores expertos, con metodología medible y certificación internacional.
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-4">
              <button
                onClick={onOpenChat}
                className="inline-flex items-center gap-2 rounded-full bg-ink px-6 py-3.5 text-sm font-medium text-cream shadow-md transition hover:bg-ink/90 hover:translate-y-[-1px] cursor-pointer"
              >
                <Sparkles size={16} className="text-gold" />
                Iniciar solicitud de admisión
              </button>
              <a
                href="#programas"
                className="rounded-full bg-white/60 px-6 py-3.5 text-sm font-medium text-ink ring-1 ring-black/5 backdrop-blur-md transition hover:bg-white/90"
              >
                Ver programas académicos
              </a>
            </div>

            <div className="mt-8 flex items-center gap-8 sm:gap-12 border-t border-black/5 pt-6">
              <div>
                <div className="text-2xl sm:text-3xl font-light font-display text-ink">94%</div>
                <div className="text-xs text-ink/60 font-medium">Tasa de aprobación</div>
              </div>
              <div className="h-8 w-px bg-black/10" />
              <div>
                <div className="text-2xl sm:text-3xl font-light font-display text-ink">6.2×</div>
                <div className="text-xs text-ink/60 font-medium">Más práctica conversacional</div>
              </div>
              <div className="h-8 w-px bg-black/10" />
              <div>
                <div className="text-2xl sm:text-3xl font-light font-display text-ink">12k+</div>
                <div className="text-xs text-ink/60 font-medium">Estudiantes certificados</div>
              </div>
            </div>
          </div>

          <div className="col-span-12 lg:col-span-5 mt-4 lg:mt-0 animate-rise animation-delay-200">
            <div className="relative overflow-hidden rounded-3xl bg-white/40 p-2 sm:p-2.5 ring-1 ring-black/10 backdrop-blur-md shadow-lg">
              <img
                src={campusHero}
                alt="Campus principal de Academia Lumina con más de 5.000 estudiantes activos"
                className="w-full h-[280px] sm:h-[360px] lg:h-[460px] rounded-2xl object-cover object-center transition duration-500 hover:scale-[1.01]"
                loading="eager"
              />
              <div className="absolute bottom-4 left-4 sm:bottom-5 sm:left-5 inline-flex items-center gap-3 rounded-2xl bg-white/90 p-2.5 sm:p-3 ring-1 ring-black/10 backdrop-blur-md shadow-md max-w-[calc(100%-2rem)]">
                <div className="grid size-9 sm:size-10 shrink-0 place-items-center rounded-xl bg-gold/50 font-display font-bold text-ink">
                  <GraduationCap size={18} className="text-ink" />
                </div>
                <div className="min-w-0 pr-1">
                  <div className="text-xs font-bold text-ink truncate">Campus Lumina · +5.000 Estudiantes</div>
                  <div className="text-[11px] text-ink/70 font-medium truncate">Sede universitaria y programas virtuales</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Programs Section */}
        <section id="programas" className="py-8 lg:py-10">
          <div className="rounded-3xl bg-white/40 p-6 ring-1 ring-black/5 backdrop-blur-md md:p-10 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-[11px] uppercase tracking-[0.2em] text-ink/50 font-semibold">Oferta Académica</span>
                <h2 className="mt-2 text-3xl font-light font-display text-ink">Explora nuestros programas</h2>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {["Todos", "Inglés", "Francés", "Portugués"].map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setActiveFilter(filter)}
                    className={`rounded-full px-4 py-2 text-xs font-medium transition ${
                      activeFilter === filter
                        ? "bg-ink text-cream shadow-sm"
                        : "bg-white/50 text-ink ring-1 ring-black/5 hover:bg-white/80"
                    }`}
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
              {filteredPrograms.map((program) => (
                <article
                  key={program.id}
                  className="group relative flex flex-col justify-between rounded-2xl bg-white/60 p-6 ring-1 ring-black/5 transition duration-300 hover:-translate-y-1 hover:bg-white/90 hover:shadow-md"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full px-3 py-1 text-[11px] font-semibold ${
                            program.color === "gold"
                              ? "bg-gold/40 text-ink"
                              : program.color === "rose"
                                ? "bg-rose/60 text-ink"
                                : "bg-brand/30 text-ink"
                          }`}
                        >
                          {program.language}
                        </span>
                        {program.tag && (
                          <span className="rounded-full bg-black/5 px-2.5 py-0.5 text-[10px] font-medium text-ink/60">
                            {program.tag}
                          </span>
                        )}
                      </div>
                      <span className="text-xs font-semibold text-ink/50">{program.level}</span>
                    </div>

                    <h3 className="mt-5 text-xl font-display text-ink font-normal">{program.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-ink/70">{program.description}</p>
                  </div>

                  <div className="mt-6 border-t border-black/5 pt-4">
                    <div className="flex items-center justify-between text-xs text-ink/60 mb-2">
                      <span>{program.duration}</span>
                      <span>{program.modality}</span>
                    </div>
                    {program.price && (
                      <div className="text-[11px] font-semibold text-brand mb-3">
                        Tarifa oficial: {program.price}
                      </div>
                    )}
                    <button
                      onClick={onOpenChat}
                      className="inline-flex w-full items-center justify-between rounded-xl bg-ink/5 px-4 py-2.5 text-xs font-semibold text-ink transition group-hover:bg-ink group-hover:text-cream"
                    >
                      <span>Consultar programa</span>
                      <ArrowRight size={14} className="transition group-hover:translate-x-1" />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        {/* Benefits Section */}
        <section className="py-8 lg:py-10">
          <div className="mb-6">
            <span className="text-[11px] uppercase tracking-[0.2em] text-ink/50 font-semibold">Diferenciales</span>
            <h2 className="mt-1 text-2xl sm:text-3xl font-light font-display text-ink">Un método pensado para adultos y profesionales</h2>
          </div>
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
            {benefits.map((benefit) => (
              <div
                key={benefit.title}
                className="rounded-2xl bg-white/40 p-5 ring-1 ring-black/5 backdrop-blur-sm transition duration-300 hover:bg-white/70 hover:shadow-sm"
              >
                <div className="grid size-10 place-items-center rounded-2xl bg-white/70 ring-1 ring-black/5 text-brand shadow-xs">
                  <benefit.icon size={18} />
                </div>
                <h3 className="mt-4 text-base font-semibold text-ink">{benefit.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-ink/70">{benefit.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Process Section */}
        <section id="proceso" className="py-8 lg:py-10">
          <div className="mb-6 flex items-end justify-between">
            <div>
              <span className="text-[11px] uppercase tracking-[0.2em] text-ink/50 font-semibold">Metodología</span>
              <h2 className="mt-1 text-2xl sm:text-3xl font-light font-display text-ink">Cuatro pasos hacia tu certificación</h2>
              <p className="mt-1 text-sm text-ink/65">Un flujo guiado desde tu primera consulta hasta el examen oficial.</p>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-5 md:grid-cols-4">
            {steps.map((step, index) => (
              <div
                key={step.number}
                className={`relative rounded-2xl p-5 ring-1 ring-black/5 backdrop-blur-sm transition duration-300 ${
                  index === 3 ? "bg-ink text-cream shadow-md" : "bg-white/40 text-ink hover:bg-white/70"
                }`}
              >
                <span className={`text-xs font-bold font-display ${index === 3 ? "text-gold" : "text-brand"}`}>
                  {step.number}
                </span>
                <h3 className="mt-2.5 text-base font-semibold">{step.title}</h3>
                <p className={`mt-1.5 text-sm leading-relaxed ${index === 3 ? "text-cream/75" : "text-ink/70"}`}>
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Testimonial + Certification Section */}
        <section id="certificacion" className="grid grid-cols-12 gap-6 lg:gap-8 py-8 lg:py-10">
          <div className="col-span-12 md:col-span-7">
            <div className="flex h-full flex-col justify-between rounded-3xl bg-white/40 p-6 ring-1 ring-black/5 backdrop-blur-md shadow-sm md:p-8">
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-brand font-semibold">Testimonios de Egresados</div>
                <blockquote className="mt-4 font-display text-xl leading-snug text-ink md:text-2xl font-light">
                  “Pasé de B1 a C1 en inglés en cinco meses con Lumina. El enfoque de retroalimentación semanal y práctica real me permitió asumir mi rol internacional.”
                </blockquote>
              </div>
              <div className="mt-6 flex items-center gap-4 border-t border-black/5 pt-5">
                <img
                  src={testimonialAvatar}
                  alt="Mariana S. — Directora de Operaciones"
                  className="size-12 rounded-full object-cover ring-2 ring-white shadow-sm"
                />
                <div>
                  <div className="text-sm font-semibold text-ink">Mariana S.</div>
                  <div className="text-xs text-ink/60">Directora de Operaciones · Certificada C1</div>
                </div>
              </div>
            </div>
          </div>

          <div className="col-span-12 md:col-span-5">
            <div className="flex h-full flex-col justify-between rounded-3xl bg-ink p-6 text-cream shadow-md md:p-8">
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-gold font-semibold">Validez Internacional</div>
                <h3 className="mt-3 text-2xl font-light font-display">Certificación Verificable</h3>
                <p className="mt-2.5 text-sm leading-relaxed text-cream/75">
                  Cada programa concluye con un examen evaluado por examinadores certificados y un diploma con código criptográfico de verificación pública.
                </p>
              </div>
              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-cream/10 p-4 ring-1 ring-cream/15 backdrop-blur-xs">
                  <div className="text-2xl font-display font-light text-gold">MCER</div>
                  <div className="text-xs text-cream/70 mt-1">A1 – C2 Global</div>
                </div>
                <div className="rounded-2xl bg-cream/10 p-4 ring-1 ring-cream/15 backdrop-blur-xs">
                  <div className="text-2xl font-display font-light text-gold">98%</div>
                  <div className="text-xs text-cream/70 mt-1">Aprobación en primer intento</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Classroom photo banner */}
        <section className="py-8 lg:py-10">
          <div className="relative overflow-hidden rounded-3xl ring-1 ring-black/5 shadow-lg">
            <img
              src={classroomImg}
              alt="Estudiantes en aula de Academia Lumina"
              className="h-[320px] w-full object-cover md:h-[400px]"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-ink/80 via-ink/30 to-transparent" />
            <div className="absolute bottom-6 left-6 right-6 text-cream md:bottom-10 md:left-10 md:right-10">
              <h2 className="text-2xl font-light font-display md:text-3xl">Una comunidad que aprende con propósito</h2>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-cream/85 md:text-base">
                Aulas reducidas, horarios ejecutivos y asesores apasionados por tu evolución lingüística y profesional.
              </p>
              <button
                onClick={onOpenChat}
                className="mt-5 inline-flex items-center gap-2 rounded-full bg-cream px-6 py-3 text-xs font-semibold text-ink shadow-md transition hover:bg-white cursor-pointer"
              >
                Hablar con un asesor ahora
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="mt-8 border-t border-black/5 bg-white/30 backdrop-blur-xs">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-6 px-6 py-8 text-sm text-ink/65">
          <div className="flex items-center gap-2.5">
            <div className="grid size-8 place-items-center rounded-xl bg-white/80 ring-1 ring-black/5 text-brand font-bold font-display">
              L
            </div>
            <span className="font-display text-lg font-medium text-ink">Academia Lumina</span>
          </div>
          <div className="flex flex-wrap gap-x-8 gap-y-2 text-xs font-medium">
            <a href="#inicio" className="transition hover:text-brand">Inicio</a>
            <a href="#programas" className="transition hover:text-brand">Programas</a>
            <a href="#proceso" className="transition hover:text-brand">Metodología</a>
            <a href="#certificacion" className="transition hover:text-brand">Certificación</a>
            <button onClick={onNavigateAdmin} className="transition hover:text-brand cursor-pointer">Portal del asesor</button>
          </div>
          <span className="text-xs text-ink/50">© 2026 Academia Lumina · Todos los derechos reservados</span>
        </div>
      </footer>
    </div>
  );
}
