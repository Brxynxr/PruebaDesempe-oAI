import React, { useState, useEffect } from 'react';
import LandingPage from './components/LandingPage';
import FloatingChat from './components/FloatingChat';
import AdminLogin from './components/AdminLogin';
import AdminDashboard from './components/AdminDashboard';
import { getAdminToken, removeAdminToken } from './services/api';

export default function App() {
  const [currentPath, setCurrentPath] = useState(() => window.location.pathname);
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(() => !!getAdminToken());
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Sync with browser navigation
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
    setIsAdminAuthenticated(!!getAdminToken());
  };

  const handleOpenChat = () => {
    setIsChatOpen(true);
  };

  const handleLoginSuccess = () => {
    setIsAdminAuthenticated(true);
    navigateTo('/admin');
  };

  const handleLogout = () => {
    removeAdminToken();
    setIsAdminAuthenticated(false);
    navigateTo('/admin/login');
  };

  // Admin Routes
  if (currentPath.startsWith('/admin')) {
    if (isAdminAuthenticated) {
      return (
        <AdminDashboard
          onLogout={handleLogout}
          onBackToSite={() => navigateTo('/')}
        />
      );
    }
    return (
      <AdminLogin
        onLoginSuccess={handleLoginSuccess}
        onBackToLanding={() => navigateTo('/')}
      />
    );
  }

  // Public Landing Page
  return (
    <>
      <LandingPage
        onOpenChat={handleOpenChat}
        onNavigateAdmin={() => navigateTo(isAdminAuthenticated ? '/admin' : '/admin/login')}
      />
      <FloatingChat isOpen={isChatOpen} setIsOpen={setIsChatOpen} />
    </>
  );
}
