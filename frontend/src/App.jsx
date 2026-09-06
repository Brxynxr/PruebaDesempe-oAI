import React, { useState, useEffect } from 'react';
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
import AdminLogin from './components/AdminLogin';
import AdminDashboard from './components/AdminDashboard';
import { getAdminToken } from './services/api';
import './App.css';

function MainAppContent() {
  const [currentPath, setCurrentPath] = useState(() => window.location.pathname);
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(() => !!getAdminToken());
  const [activeTab, setActiveTab] = useState('home'); // 'home' | 'modalities'
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Listen to browser navigation popstate
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
      setIsAdminAuthenticated(!!getAdminToken());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateTo = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
  };

  const handleOpenChat = () => {
    setIsChatOpen(true);
  };

  const handleLoginSuccess = () => {
    setIsAdminAuthenticated(true);
    navigateTo('/admin');
  };

  const handleLogout = () => {
    setIsAdminAuthenticated(false);
    navigateTo('/admin/login');
  };

  // If in admin route
  if (currentPath.startsWith('/admin')) {
    return (
      <div className="app admin-portal-theme">
        <ParticleBackground />
        {isAdminAuthenticated ? (
          <AdminDashboard
            onLogout={handleLogout}
            onBackToSite={() => navigateTo('/')}
          />
        ) : (
          <AdminLogin
            onLoginSuccess={handleLoginSuccess}
            onBackToSite={() => navigateTo('/')}
          />
        )}
      </div>
    );
  }

  // Public Landing Page (Unchanged design, no links to /admin)
  return (
    <div className={`app theme-${activeTab}`}>
      {/* Global Golden Particle Ambient Background */}
      <ParticleBackground />

      {/* Persistent Navbar with SPA Tabs, Theme Toggle, Language Selector & Advisor Login */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenChat={handleOpenChat}
        onNavigateToAdmin={() => navigateTo(isAdminAuthenticated ? '/admin' : '/admin/login')}
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
      <Footer onNavigateToAdmin={() => navigateTo(isAdminAuthenticated ? '/admin' : '/admin/login')} />
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
