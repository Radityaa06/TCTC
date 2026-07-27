import React from 'react';
import { Layers, ArrowRight } from 'lucide-react';

export default function ColumnMapper({ fields, datasetColumns }) {
  if (!fields || fields.length === 0) {
    return (
      <div className="cyber-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <span className="step-chip">03</span>
          <div>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: '700' }}>
              Field Mapping Preview
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Interactive column matching table
            </p>
          </div>
        </div>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', background: 'rgba(8, 12, 22, 0.4)', padding: '24px', borderRadius: '16px', textAlign: 'center' }}>
          Inspect target URL above to view dynamic field matching preview.
        </p>
      </div>
    );
  }

  return (
    <div className="cyber-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <span className="step-chip">03</span>
        <div>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.3rem', fontWeight: '700' }}>
            Field Mapping Preview
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Interactive column matching table
          </p>
        </div>
      </div>

      <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
        <table className="mapping-table">
          <thead>
            <tr>
              <th style={{ padding: '12px 14px' }}>Target Web Field</th>
              <th style={{ textAlign: 'center', padding: '12px 14px' }}>Match</th>
              <th style={{ padding: '12px 14px' }}>Uploaded Excel Header</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((f, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: '600', color: 'var(--text-primary)', padding: '12px 14px' }}>{f.label}</td>
                <td style={{ textAlign: 'center', color: 'var(--cyan-bright)', padding: '12px 14px' }}><ArrowRight size={16} /></td>
                <td style={{ color: 'var(--violet)', fontWeight: '700', padding: '12px 14px' }}>
                  {datasetColumns && datasetColumns.includes(f.label) ? f.label : f.name || f.key}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
