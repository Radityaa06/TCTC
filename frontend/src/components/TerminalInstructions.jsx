import React from 'react';
import { Terminal, Code, Cpu } from 'lucide-react';

export default function TerminalInstructions() {
  return (
    <div className="cyber-card col-span-2">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
        <span className="step-chip">04</span>
        <div>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: '700' }}>
            Execute Local Automation
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Start the automation directly from your computer to see it typing live!
          </p>
        </div>
      </div>

      <div style={{ 
        background: 'rgba(56, 189, 248, 0.1)', 
        border: '1px solid rgba(56, 189, 248, 0.3)', 
        borderRadius: '12px', 
        padding: '24px',
        color: 'var(--text-secondary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <Cpu className="text-cyan" size={24} />
          <h4 style={{ color: 'var(--text-main)', fontSize: '1.1rem', fontWeight: '600' }}>Local Execution Mode</h4>
        </div>
        
        <p style={{ marginBottom: '20px', lineHeight: '1.6' }}>
          The Live Automation Dashboard has been removed as requested. To bypass Cloudflare and see the robot typing on your own screen, please run the automation locally using your terminal.
        </p>

        <div style={{ marginBottom: '12px', fontWeight: '600', color: 'var(--text-main)' }}>
          Run this command in your computer's terminal/command prompt:
        </div>

        <div style={{ 
          background: '#040810', 
          padding: '16px 20px', 
          borderRadius: '8px', 
          fontFamily: 'monospace', 
          color: '#10b981',
          border: '1px solid #1f2937',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          overflowX: 'auto'
        }}>
          <Terminal size={18} color="var(--text-secondary)" />
          <span>python3 start_bot.py</span>
        </div>
      </div>
    </div>
  );
}
