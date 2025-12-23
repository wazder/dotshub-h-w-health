import React, { useState, useEffect } from 'react';

const SettingsView = ({ onBack }) => {
    // Initialize theme from document attribute or default
    const [theme, setTheme] = useState(() => {
        return document.documentElement.getAttribute('data-theme') || 'dark';
    });
    const [notifications, setNotifications] = useState(true);
    const [autoAnalysis, setAutoAnalysis] = useState(true);

    // Apply theme change
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    return (
        <div className="w-full h-full p-8 overflow-y-auto bg-[var(--bg-dark)]">
            <div className="max-w-2xl mx-auto space-y-8">

                {/* Back Button */}
                <button
                    onClick={onBack}
                    className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-main)] transition group"
                >
                    <svg className="group-hover:-translate-x-1 transition-transform" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5" /><path d="M12 19l-7-7 7-7" /></svg>
                    <span>Back to Home</span>
                </button>

                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-[var(--text-main)] mb-2">Settings</h1>
                    <p className="text-[var(--text-muted)]">Manage your preferences and system configuration.</p>
                </div>

                {/* System Preferences Section */}
                <div className="card p-6 border border-[var(--border)]">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-[var(--text-main)]">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg>
                        Sistem Tercihleri
                    </h2>

                    <div className="space-y-6">
                        <div className="flex items-center justify-between py-3 border-b border-[var(--border)]">
                            <div>
                                <h3 className="font-medium text-[var(--text-main)]">Theme Mode</h3>
                                <p className="text-sm text-[var(--text-muted)]">Select your preferred interface appearance.</p>
                            </div>
                            <div className="flex bg-[var(--bg-dark)] p-1 rounded-lg border border-[var(--border)]">
                                <button
                                    className={`px-4 py-1.5 rounded transition text-sm ${theme === 'light' ? 'bg-[var(--bg-card)] shadow text-[var(--text-main)]' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}`}
                                    onClick={() => setTheme('light')}
                                >
                                    Light
                                </button>
                                <button
                                    className={`px-4 py-1.5 rounded transition text-sm ${theme === 'dark' ? 'bg-[var(--bg-card)] shadow text-[var(--text-main)]' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}`}
                                    onClick={() => setTheme('dark')}
                                >
                                    Dark
                                </button>
                            </div>
                        </div>

                        <div className="flex items-center justify-between py-3 border-b border-[var(--border)]">
                            <div>
                                <h3 className="font-medium text-[var(--text-main)]">Auto Analysis</h3>
                                <p className="text-sm text-[var(--text-muted)]">Automatically start analysis after upload.</p>
                            </div>
                            <button
                                onClick={() => setAutoAnalysis(!autoAnalysis)}
                                className={`w-12 h-6 rounded-full transition relative ${autoAnalysis ? 'bg-[var(--success)]' : 'bg-[var(--border)]'}`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white absolute top-1 left-1 transition-transform ${autoAnalysis ? 'translate-x-6' : ''}`}></div>
                            </button>
                        </div>

                        <div className="flex items-center justify-between py-3">
                            <div>
                                <h3 className="font-medium text-[var(--text-main)]">Notifications</h3>
                                <p className="text-sm text-[var(--text-muted)]">Get alerts for completed analyses.</p>
                            </div>
                            <button
                                onClick={() => setNotifications(!notifications)}
                                className={`w-12 h-6 rounded-full transition relative ${notifications ? 'bg-[var(--primary)]' : 'bg-[var(--border)]'}`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white absolute top-1 left-1 transition-transform ${notifications ? 'translate-x-6' : ''}`}></div>
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default SettingsView;
