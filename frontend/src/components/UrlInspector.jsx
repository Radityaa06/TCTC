import React, { useState } from 'react';
import { Globe, Search, Download, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';

export default function UrlInspector({ onFieldsExtracted }) {
  const [url, setUrl] = useState('https://quiz.toitctc.com/');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleInspect = async () => {
    if (!url) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/inspect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || 'Inspection failed');

      setResult(data);
      if (onFieldsExtracted) onFieldsExtracted(data.fields);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTemplate = () => {
    window.location.href = 'http://127.0.0.1:8000/api/download-template';
  };

  return (
    <div className="cyber-card col-span-2">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <span className="step-chip">01</span>
        <div>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: '700' }}>
            Target Website Form Inspector
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Paste target URL to dynamically extract form schemas and generate custom Excel templates
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Globe style={{ position: 'absolute', left: '18px', top: '50%', transform: 'translateY(-50%)', color: 'var(--cyan-bright)', width: '20px' }} />
          <input
            type="text"
            className="cyber-input"
            style={{ paddingLeft: '52px' }}
            placeholder="Paste target website URL (e.g. https://quiz.toitctc.com/)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>

        <button className="btn-neon" onClick={handleInspect} disabled={loading} style={{ whiteSpace: 'nowrap' }}>
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
          {loading ? 'Inspecting DOM...' : 'Inspect Web Form'}
        </button>
      </div>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--rose)', fontSize: '0.9rem', marginTop: '14px', background: 'rgba(244, 63, 94, 0.12)', padding: '12px 18px', borderRadius: '12px', border: '1px solid rgba(244, 63, 94, 0.25)' }}>
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div style={{ marginTop: '24px', background: 'rgba(8, 12, 22, 0.7)', padding: '24px', borderRadius: '18px', border: '1px solid var(--border-glass)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--emerald)', fontWeight: '700', fontSize: '1rem' }}>
              <CheckCircle2 size={22} />
              <span>Extracted {result.fields.length} Required Fields ({result.title})</span>
            </div>
            <button className="btn-glass-action" onClick={handleDownloadTemplate} style={{ fontSize: '0.88rem' }}>
              <Download size={18} style={{ color: 'var(--cyan-bright)' }} />
              Download Excel Template (.xlsx)
            </button>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            {result.fields.map((f, idx) => (
              <span key={idx} className="feature-badge">
                {f.label} <span style={{ opacity: 0.65 }}>({f.name || f.key})</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
