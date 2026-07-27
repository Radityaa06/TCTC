import React from 'react';
import { Cpu, ShieldCheck } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="brand-wrapper">
        <div className="brand-logo">
          <Cpu style={{ color: '#ffffff', width: '24px', height: '24px' }} />
        </div>
        <div>
          <div className="brand-name">AUTOFORM AI</div>
          <div className="brand-tag">UNIVERSAL WEB AUTOMATION PLATFORM</div>
        </div>
      </div>
      <div className="status-badge">
        <div className="pulse-dot"></div>
        <span>AUTOMATION ENGINE ONLINE</span>
      </div>
    </nav>
  );
}
