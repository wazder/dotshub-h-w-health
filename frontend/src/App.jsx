import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import LoginPage from './components/LoginPage';
import ProfileView from './components/ProfileView';
import SettingsView from './components/SettingsView';
import PatientDetailView from './components/PatientDetailView';


function App() {
  const [isLoggedin, setIsLoggedIn] = useState(true);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard' | 'profile' | 'settings' | 'patient_detail'
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogin = (username) => {
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setIsDropdownOpen(false);
    setCurrentView('dashboard');
  };

  const navigateTo = (view) => {
    setCurrentView(view);
    setIsDropdownOpen(false);
  };

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    setCurrentView('patient_detail');
  };

  const handleSearch = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      // Mock lookup based on ID
      const mockPatient = {
        id: searchQuery,
        age: 45, // default mock
        gender: 'Unknown',
        diagnosis: 'Pending Lookup'
      };
      handlePatientSelect(mockPatient);
      setSearchQuery('');
    }
  };

  if (!isLoggedin) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const renderContent = () => {
    switch (currentView) {
      case 'profile': return <ProfileView onBack={() => setCurrentView('dashboard')} />;
      case 'settings': return <SettingsView onBack={() => setCurrentView('dashboard')} />;
      case 'patient_detail': return <PatientDetailView patient={selectedPatient} onBack={() => setCurrentView('dashboard')} />;
      default: return <Dashboard onSelectPatient={handlePatientSelect} />;
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-dark)] text-[var(--text-main)] w-full h-screen overflow-hidden flex flex-col">
      {/* Top Header */}
      <header className="h-14 border-b border-[var(--border)] bg-[var(--bg-card)] flex items-center px-6 justify-between flex-shrink-0 relative z-50">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setCurrentView('dashboard')}>
          <div className="w-6 h-6 bg-[var(--primary)] rounded flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M2 12h20" /></svg>
          </div>
          <span className="font-bold text-lg tracking-tight">Ellie <span className="text-[var(--text-muted)] font-normal text-sm"></span></span>
        </div>

        {/* Search Bar */}
        <div className="absolute left-1/2 -translate-x-1/2 w-96 max-w-lg hidden md:block">
          <div className="relative group">
            <svg className="absolute left-3 top-2.5 text-[var(--text-muted)] group-focus-within:text-[var(--primary)] transition" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
            <input
              type="text"
              placeholder="Search Patient ID (Press Enter)..."
              className="w-full bg-[var(--bg-dark)] border border-[var(--border)] rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] transition"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearch}
            />
          </div>
        </div>

        <div className="relative">
          <div
            className="flex items-center gap-4 cursor-pointer hover:bg-[var(--bg-card-hover)] p-2 rounded transition"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          >
            <span className="text-sm text-[var(--text-muted)]">Dr. Umut G.</span>
            <div className="w-8 h-8 rounded-full bg-[var(--bg-card-hover)] border border-[var(--border)] overflow-hidden">
              <img src="https://ui-avatars.com/api/?name=Umut+G&background=0D8ABC&color=fff" alt="User" />
            </div>
          </div>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute top-full right-0 mt-2 w-48 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200">
              <div className="p-2">
                <div className="text-xs text-[var(--text-muted)] font-bold px-3 py-2 uppercase tracking-wider">Account</div>
                <button
                  onClick={() => navigateTo('profile')}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--bg-card-hover)] rounded flex items-center gap-2"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                  Profile
                </button>
                <button
                  onClick={() => navigateTo('settings')}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--bg-card-hover)] rounded flex items-center gap-2"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
                  Settings
                </button>
                <div className="h-px bg-[var(--border)] my-1"></div>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-400/10 rounded flex items-center gap-2"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden relative" onClick={() => isDropdownOpen && setIsDropdownOpen(false)}>
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
