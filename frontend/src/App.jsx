import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import ProgramsSection from './components/ProgramsSection';
import FloatingChat from './components/FloatingChat';
import './App.css';

export default function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="app">
      <Navbar />
      <Hero onOpenChat={() => setIsChatOpen(true)} />
      <ProgramsSection />
      <FloatingChat isOpen={isChatOpen} setIsOpen={setIsChatOpen} />
    </div>
  );
}
