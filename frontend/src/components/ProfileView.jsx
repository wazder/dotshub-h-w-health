import React from 'react';

const ProfileView = ({ onBack }) => {
    // Mock History Data
    const recentScans = [
        { id: '10293', date: '2023-10-24', type: 'MRI - Brain (Axial)', status: 'Verified' },
        { id: '10292', date: '2023-10-24', type: 'MRI - Brain (Sagittal)', status: 'Pending Review' },
        { id: '10288', date: '2023-10-22', type: 'fMRI - Resting State', status: 'Verified' },
        { id: '10285', date: '2023-10-20', type: 'CT - Head w/ Contrast', status: 'Archived' },
        { id: '10271', date: '2023-10-18', type: 'MRI - Brain (T2-Weighted)', status: 'Verified' },
    ];

    return (
        <div className="w-full h-full p-8 overflow-y-auto bg-[var(--bg-dark)]">
            <div className="max-w-4xl mx-auto space-y-8">

                {/* Back Button */}
                <button
                    onClick={onBack}
                    className="flex items-center gap-2 text-[var(--text-muted)] hover:text-white transition group"
                >
                    <svg className="group-hover:-translate-x-1 transition-transform" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5" /><path d="M12 19l-7-7 7-7" /></svg>
                    <span>Back to Dashboard</span>
                </button>

                {/* Header Card */}
                <div className="card p-8 flex items-center gap-8 relative overflow-hidden border border-[var(--border)]">
                    <div className="absolute top-0 right-0 p-32 bg-[var(--primary)] opacity-[0.03] rounded-full blur-3xl translate-x-1/2 -translate-y-1/2"></div>

                    <div className="w-32 h-32 rounded-full border-4 border-[var(--bg-card)] shadow-2xl overflow-hidden relative z-10">
                        <img src="https://ui-avatars.com/api/?name=Umut+G&background=0D8ABC&color=fff&size=200" alt="Dr. Umut G." className="w-full h-full object-cover" />
                    </div>

                    <div className="flex-1 relative z-10">
                        <h1 className="text-3xl font-bold text-white mb-2">Dr. Umut G.</h1>
                        <div className="flex items-center gap-4 text-[var(--text-muted)] mb-4">
                            <span className="flex items-center gap-1">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
                                Senior Radiologist
                            </span>
                            <span className="w-1 h-1 bg-[var(--border)] rounded-full"></span>
                            <span className="flex items-center gap-1">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18" /><path d="M5 21V7l8-4 8 4v14" /><path d="M8 21v-8a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v8" /></svg>
                                NeuroGuard Medical Center
                            </span>
                        </div>
                        <div className="flex gap-3">
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-4">
                    <div className="card p-6 border-l-4 border-[var(--primary)]">
                        <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider block mb-1">Total Scans Analyzed</span>
                        <span className="text-3xl font-bold">1,204</span>
                    </div>
                    <div className="card p-6 border-l-4 border-[var(--success)]">
                        <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider block mb-1">Accuracy Rate</span>
                        <span className="text-3xl font-bold">99.2%</span>
                    </div>
                    <div className="card p-6 border-l-4 border-[var(--accent)]">
                        <span className="text-xs text-[var(--text-muted)] uppercase tracking-wider block mb-1">Pending Reviews</span>
                        <span className="text-3xl font-bold">4</span>
                    </div>
                </div>

                {/* Recent History Table */}
                <div className="card overflow-hidden border border-[var(--border)]">
                    <div className="p-4 border-b border-[var(--border)] bg-[var(--bg-card-hover)]/30">
                        <h3 className="font-bold flex items-center gap-2">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
                            Recent Scan History
                        </h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead>
                                <tr className="border-b border-[var(--border)] text-[var(--text-muted)]">
                                    <th className="p-4 font-medium">Date</th>
                                    <th className="p-4 font-medium">Patient ID</th>
                                    <th className="p-4 font-medium">Scan Type</th>
                                    <th className="p-4 font-medium">Status</th>
                                    <th className="p-4 font-medium text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recentScans.map((scan, i) => (
                                    <tr key={i} className="border-b border-[var(--border)] hover:bg-[var(--bg-card-hover)] transition group">
                                        <td className="p-4 font-mono text-[var(--text-muted)]">{scan.date}</td>
                                        <td className="p-4 font-bold">#{scan.id}</td>
                                        <td className="p-4">{scan.type}</td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs border ${scan.status === 'Verified' ? 'bg-green-900/20 text-green-300 border-green-900' :
                                                scan.status === 'Pending Review' ? 'bg-yellow-900/20 text-yellow-300 border-yellow-900' :
                                                    'bg-gray-800 text-gray-400 border-gray-700'
                                                }`}>
                                                {scan.status}
                                            </span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <button className="text-[var(--primary)] hover:underline opacity-0 group-hover:opacity-100 transition">View Report</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="p-4 text-center border-t border-[var(--border)]">
                        <button className="text-sm text-[var(--text-muted)] hover:text-white transition">View Full History</button>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default ProfileView;
