import React from 'react';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <div className="min-h-screen bg-[var(--bg-dark)] text-[var(--text-main)] w-full h-screen overflow-hidden flex flex-col">
      {/* Top Header */}
      <header className="h-14 border-b border-[var(--border)] bg-[var(--bg-card)] flex items-center px-6 justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-[var(--primary)] rounded flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M2 12h20" /></svg>
          </div>
          <span className="font-bold text-lg tracking-tight">NeuroGuard <span className="text-[var(--text-muted)] font-normal text-sm">CDSS</span></span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-[var(--text-muted)]">Dr. Umut G.</span>
          <div className="w-8 h-8 rounded-full bg-[var(--bg-card-hover)] border border-[var(--border)]"></div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden relative">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
