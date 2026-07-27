import React, { useState } from 'react';
import { UploadCloud, FileSpreadsheet, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function FileUpload({ onDatasetUploaded }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');

      setInfo(data);
      if (onDatasetUploaded) onDatasetUploaded(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="cyber-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <span className="step-chip">02</span>
        <div>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: '700' }}>
            Upload Dataset File
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Upload candidate dataset (.xlsx, .xls, or .csv)
          </p>
        </div>
      </div>

      <label style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 24px',
        border: '2px dashed var(--border-glass)',
        borderRadius: '18px',
        background: 'rgba(8, 12, 22, 0.5)',
        cursor: 'pointer',
        transition: 'all 0.25s ease'
      }}
      onMouseEnter={(e) => e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.45)'}
      onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-glass)'}
      >
        <div style={{
          width: '60px',
          height: '60px',
          borderRadius: '18px',
          background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(139, 92, 246, 0.2))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '14px',
          boxShadow: '0 0 20px rgba(6, 182, 212, 0.2)'
        }}>
          <UploadCloud size={32} style={{ color: 'var(--cyan-bright)' }} />
        </div>

        <span style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
          {file ? file.name : 'Drag & drop Excel file here or click to browse'}
        </span>
        <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '6px' }}>
          Supports .xlsx, .xls, and .csv files
        </span>
        <input type="file" accept=".xlsx, .xls, .csv" onChange={handleFileChange} style={{ display: 'none' }} />
      </label>

      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--rose)', fontSize: '0.88rem', marginTop: '16px', background: 'rgba(244, 63, 94, 0.12)', padding: '12px 16px', borderRadius: '12px' }}>
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {info && (
        <div style={{ marginTop: '18px', color: 'var(--emerald)', fontSize: '0.92rem', display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(16, 185, 129, 0.12)', padding: '12px 18px', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
          <CheckCircle2 size={20} />
          <span>Loaded {info.total_rows} candidate records ({info.columns.length} columns).</span>
        </div>
      )}
    </div>
  );
}
