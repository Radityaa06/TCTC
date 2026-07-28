import React, { useState } from 'react';
import { Play, Pause, RefreshCw, Sparkles, Terminal, Monitor } from 'lucide-react';

const API_BASE = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? 'http://127.0.0.1:8000'
  : window.location.origin;

export default function AutomationDashboard({ datasetInfo }) {
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [metrics, setMetrics] = useState({ completed: 0, failed: 0, total: datasetInfo?.total_rows || 250 });
  const [liveScreenshot, setLiveScreenshot] = useState(null);
  const [logs, setLogs] = useState([
    '[SYSTEM] Universal Web Automation Console Ready.',
    '[SYSTEM] Target Web App: https://quiz.toitctc.com/',
    '[SYSTEM] Awaiting user trigger...'
  ]);

  const handleStart = async () => {
    setIsRunning(true);
    setIsPaused(false);
    setLogs((prev) => [...prev, '[START v2.0] Triggering Live Video Stream Playwright Engine...']);

    try {
      await fetch(`${API_BASE}/api/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      const eventSource = new EventSource(`${API_BASE}/api/stream`);
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.logs && Array.isArray(data.logs)) {
            for (const item of data.logs) {
              if (item.log) setLogs((prev) => [...prev, item.log]);
              if (item.metrics) setMetrics(item.metrics);
            }
          }
          if (data.log) {
            setLogs((prev) => [...prev, data.log]);
          }
          if (data.metrics) {
            setMetrics(data.metrics);
          }
          if (data.live_screenshot) {
            setLiveScreenshot(data.live_screenshot);
          }
        } catch (err) {
          console.error('SSE Parse Error:', err);
        }
      };
    } catch (err) {
      setLogs((prev) => [...prev, `[ERROR] Failed to start automation: ${err.message}`]);
      setIsRunning(false);
    }
  };

  const handlePause = async () => {
    try {
      await fetch(`${API_BASE}/api/pause`, { method: 'POST' });
      setIsPaused(true);
    } catch (err) {
      console.error('Pause error:', err);
    }
  };

  const handleResume = async () => {
    try {
      await fetch(`${API_BASE}/api/resume`, { method: 'POST' });
      setIsPaused(false);
    } catch (err) {
      console.error('Resume error:', err);
    }
  };

  const total = metrics.total || datasetInfo?.total_rows || 250;
  const completed = metrics.completed || 0;
  const failed = metrics.failed || 0;
  const progressPercent = Math.min(100, Math.round(((completed + failed) / total) * 100));

  return (
    <div className="cyber-card col-span-2">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="step-chip">04</span>
          <div>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: '700' }}>
              Live Automation Dashboard & Real-Time Browser Stream
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Live video preview of targeted site execution, pause/resume, and console stream
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          {!isRunning ? (
            <button className="btn-neon" onClick={handleStart} style={{ padding: '16px 36px' }}>
              <Sparkles size={20} />
              Start Automation
            </button>
          ) : isPaused ? (
            <button className="btn-neon" onClick={handleResume} style={{ background: 'linear-gradient(135deg, #10b981, #059669)', boxShadow: '0 10px 30px rgba(16, 185, 129, 0.4)', padding: '16px 36px' }}>
              <Play size={20} />
              Resume Automation
            </button>
          ) : (
            <button className="btn-neon" onClick={handlePause} style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)', boxShadow: '0 10px 30px rgba(245, 158, 11, 0.4)', padding: '16px 36px' }}>
              <Pause size={20} />
              Pause Automation
            </button>
          )}
        </div>
      </div>

      {/* Glowing Dynamic Progress Bar */}
      <div style={{ background: 'rgba(8, 12, 22, 0.8)', borderRadius: '14px', height: '16px', width: '100%', overflow: 'hidden', border: '1px solid var(--border-glass)', marginBottom: '24px' }}>
        <div style={{
          background: 'linear-gradient(90deg, var(--cyan-bright), var(--violet), var(--emerald))',
          height: '100%',
          width: `${progressPercent}%`,
          transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: '0 0 20px rgba(56, 189, 248, 0.6)'
        }} />
      </div>

      {/* Metrics Counter Cards */}
      <div className="metrics-row">
        <div className="metric-card-cyber c-total">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '700', letterSpacing: '0.08em' }}>TOTAL CANDIDATES</div>
          <div className="metric-number">{total}</div>
        </div>
        <div className="metric-card-cyber c-success">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '700', letterSpacing: '0.08em' }}>SUCCESSFUL</div>
          <div className="metric-number">{completed}</div>
        </div>
        <div className="metric-card-cyber c-failed">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '700', letterSpacing: '0.08em' }}>FAILED</div>
          <div className="metric-number">{failed}</div>
        </div>
        <div className="metric-card-cyber c-progress">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: '700', letterSpacing: '0.08em' }}>PROGRESS</div>
          <div className="metric-number">{progressPercent}%</div>
        </div>
      </div>

      {/* LIVE BROWSER SCREEN PREVIEW WINDOW */}
      <div style={{ margin: '28px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '12px', fontWeight: '700' }}>
          <Monitor size={18} style={{ color: 'var(--cyan-bright)' }} />
          <span>LIVE TARGET SITE BROWSER VIDEO STREAM</span>
        </div>

        <div style={{
          background: '#03060c',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: '18px',
          padding: '16px',
          minHeight: '280px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 30px rgba(6, 182, 212, 0.15)',
          overflow: 'hidden'
        }}>
          {liveScreenshot ? (
            <img
              src={liveScreenshot}
              alt="Live Target Web App Browser Stream"
              style={{ width: '100%', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.1)', objectFit: 'contain', maxHeight: '480px' }}
            />
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px 20px' }}>
              <Monitor size={48} style={{ opacity: 0.3, marginBottom: '12px', color: 'var(--cyan-bright)' }} />
              <div style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-secondary)' }}>Awaiting Live Browser Stream</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>Click 'Start Automation' to view real-time target website execution frame-by-frame</div>
            </div>
          )}
        </div>
      </div>

      {/* Terminal Console Output */}
      <div style={{ marginTop: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '12px', fontWeight: '700' }}>
          <Terminal size={18} style={{ color: 'var(--cyan-bright)' }} />
          <span>PLAYWRIGHT REAL-TIME EXECUTION CONSOLE</span>
        </div>

        <div className="terminal-box">
          {logs.map((line, idx) => (
            <div key={idx} className={`log-entry ${line.includes('Failed') || line.includes('ERROR') ? 'error' : line.includes('Success') || line.includes('Completed') ? 'success' : line.includes('PAUSE') ? 'warn' : line.includes('INIT') || line.includes('START') || line.includes('RESUME') ? 'info' : ''}`}>
              {line}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
