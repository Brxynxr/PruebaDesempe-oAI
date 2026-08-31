import React from 'react';
import { BookOpen } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="logo">
        <BookOpen size={28} />
        <span>Academia Lumina</span>
      </div>
      <ul className="nav-links">
        <li><a href="#inicio">Inicio</a></li>
        <li><a href="#programas">Programas</a></li>
        <li><a href="#modalidades">Modalidades</a></li>
        <li><a href="#contacto">Contacto</a></li>
      </ul>
    </nav>
  );
}
