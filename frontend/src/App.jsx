import React, { useState } from 'react';
import { LanguageProvider } from './context/LanguageContext';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import WhyUsSection from './components/WhyUsSection';
import ProgramsSection from './components/ProgramsSection';
import ModalitiesSection from './components/ModalitiesSection';
import HowItWorksSection from './components/HowItWorksSection';
import CertificationSection from './components/CertificationSection';
import TestimonialsSection from './components/TestimonialsSection';
import Footer from './components/Footer';
import FloatingChat from './components/FloatingChat';
import ParticleBackground from './components/ParticleBackground';
import './App.css';

function MainAppContent() {
  const [activeTab, setActiveTab] = useState('home'); // 'home' | 'modalities'
  const [isChatOpen, setIsChatOpen] = useState(false);

  const handleOpenChat = () => {
    setIsChatOpen(true);
  };

  return (
    <div className={`app theme-${activeTab}`}>
      {/* Global Golden Particle Ambient Background (Active in both Light and Dark modes) */}
      <ParticleBackground />

      {/* Persistent Navbar with SPA Tabs, Theme Toggle & Language Selector */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenChat={handleOpenChat}
      />

      {/* Main Content: 2 clean SPA Views */}
      <main className="spa-main-content">
        {activeTab === 'home' && (
          <div className="tab-view fade-in">
            <Hero onOpenChat={handleOpenChat} />
            <WhyUsSection />
            <ProgramsSection onOpenChat={handleOpenChat} />
            <TestimonialsSection />
          </div>
        )}

        {activeTab === 'modalities' && (
          <div className="tab-view fade-in">
            <ModalitiesSection />
            <HowItWorksSection />
            <CertificationSection />
          </div>
        )}
      </main>

      {/* Persistent Footer and Floating AI Chat */}
      <Footer />
      <FloatingChat isOpen={isChatOpen} setIsOpen={setIsChatOpen} />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <MainAppContent />
      </LanguageProvider>
    </ThemeProvider>
  );
}
