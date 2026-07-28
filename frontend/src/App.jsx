import React, { useState } from 'react';
import Navbar from './components/Navbar';
import UrlInspector from './components/UrlInspector';
import FileUpload from './components/FileUpload';
import ColumnMapper from './components/ColumnMapper';
import TerminalInstructions from './components/TerminalInstructions';

export default function App() {
  const [fields, setFields] = useState([]);
  const [datasetInfo, setDatasetInfo] = useState(null);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <main className="app-grid">
        <UrlInspector onFieldsExtracted={(extracted) => setFields(extracted)} />
        <FileUpload onDatasetUploaded={(info) => setDatasetInfo(info)} />
        <ColumnMapper fields={fields} datasetColumns={datasetInfo?.columns} />
        <TerminalInstructions />
      </main>

      <footer style={{ marginTop: 'auto', textAlign: 'center', padding: '24px', borderTop: '1px solid var(--border-glass)', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
        AutoForm AI Universal Web Automation Platform • Built with React & Playwright Engine
      </footer>
    </div>
  );
}
