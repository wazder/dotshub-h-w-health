import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import LoginPage from './components/LoginPage';
import ProfileView from './components/ProfileView';
import SettingsView from './components/SettingsView';
import PatientDetailView from './components/PatientDetailView';
import { getPatient } from './services/api';


function App() {
  const [isLoggedin, setIsLoggedIn] = useState(true);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard' | 'profile' | 'settings' | 'patient_detail'
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchError, setSearchError] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [cameFromResults, setCameFromResults] = useState(false);

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
    setCameFromResults(true);
    setCurrentView('patient_detail');
  };

  const handleBackFromPatientDetail = () => {
    // Dashboard'a dön (analiz sonuçları orada gösterilecek)
    setCurrentView('dashboard');
    setCameFromResults(false);
  };

  const handleSearch = async (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      setSearchError(null);
      setIsSearching(true);
      
      try {
        // Gerçek API ile hasta ara
        const patientData = await getPatient(searchQuery.trim());
        
        if (patientData) {
          const patient = {
            id: patientData.patientId || searchQuery,
            age: patientData.age || 0,
            gender: patientData.gender || 'Bilinmiyor',
            diagnosis: patientData.history?.diagnosis || 'Bilgi Yok'
          };
          setCameFromResults(false);
          handlePatientSelect(patient);
          setSearchQuery('');
        } else {
          setSearchError('Hasta bulunamadı');
        }
      } catch (error) {
        // Hasta arama hatası - sessizce hata mesajı göster
        setSearchError('Hasta bulunamadı veya bağlantı hatası');
      } finally {
        setIsSearching(false);
      }
    }
  };

  if (!isLoggedin) {
    return <LoginPage onLogin={handleLogin} />;
  }

  const renderContent = () => {
    switch (currentView) {
      case 'profile': return <ProfileView onBack={() => setCurrentView('dashboard')} />;
      case 'settings': return <SettingsView onBack={() => setCurrentView('dashboard')} />;
      case 'patient_detail': return <PatientDetailView patient={selectedPatient} onBack={handleBackFromPatientDetail} returnToResults={cameFromResults ? handleBackFromPatientDetail : null} />;
      default: return <Dashboard onSelectPatient={handlePatientSelect} />;
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-dark)] text-[var(--text-main)] w-full h-screen overflow-hidden flex flex-col">
      {/* Top Header */}
      <header className="h-14 border-b border-[var(--border)] bg-[var(--bg-card)] flex items-center px-6 justify-between flex-shrink-0 relative z-50">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setCurrentView('dashboard')}>
          <img src="/ellie.png" alt="Ellie" className="h-8 w-auto" />
        </div>

        {/* Search Bar */}
        <div className="absolute left-1/2 -translate-x-1/2 w-96 max-w-lg hidden md:block">
          <div className="relative group">
            {isSearching ? (
              <svg className="absolute left-3 top-2.5 text-[var(--primary)] animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" strokeDasharray="30" strokeDashoffset="10" />
              </svg>
            ) : (
              <svg className="absolute left-3 top-2.5 text-[var(--text-muted)] group-focus-within:text-[var(--primary)] transition" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
            )}
            <input
              type="text"
              placeholder="Hasta ID ile ara (örn: 00001)..."
              className={`w-full bg-[var(--bg-dark)] border rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 transition ${
                searchError 
                  ? 'border-red-500 focus:border-red-500 focus:ring-red-500' 
                  : 'border-[var(--border)] focus:border-[var(--primary)] focus:ring-[var(--primary)]'
              }`}
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setSearchError(null); }}
              onKeyDown={handleSearch}
              disabled={isSearching}
            />
            {searchError && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-red-900/90 text-red-200 text-xs px-3 py-1.5 rounded shadow-lg">
                {searchError}
              </div>
            )}
          </div>
        </div>

        <div className="relative">
          <div
            className="flex items-center gap-4 cursor-pointer hover:bg-[var(--bg-card-hover)] p-2 rounded transition"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          >
            <div className="w-8 h-8 rounded-full bg-[var(--primary)] border border-[var(--border)] overflow-hidden flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
            </div>
          </div>

          {/* Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute top-full right-0 mt-2 w-48 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200">
              <div className="p-2">
                <div className="text-xs text-[var(--text-muted)] font-bold px-3 py-2 uppercase tracking-wider">Hesap</div>
                <button
                  onClick={() => navigateTo('profile')}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--bg-card-hover)] rounded flex items-center gap-2"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                  Profil
                </button>
                <button
                  onClick={() => navigateTo('settings')}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--bg-card-hover)] rounded flex items-center gap-2"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
                  Ayarlar
                </button>
                <div className="h-px bg-[var(--border)] my-1"></div>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-red-400/10 rounded flex items-center gap-2"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                  Çıkış Yap
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
