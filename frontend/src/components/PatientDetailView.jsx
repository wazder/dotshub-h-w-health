import React from 'react';

const PatientDetailView = ({ patient, onBack }) => {
    // Mock extended data
    const patientData = {
        name: 'Sarah Connor', // Placeholder, would come from real DB
        id: patient?.id || 'PT-Unknown',
        age: patient?.age || 45,
        gender: 'Female',
        mriScans: [
            { date: '2023-11-15', type: 'T1-Weighted', status: 'Abnormal' },
            { date: '2023-09-02', type: 'T2-Weighted', status: 'Normal' },
            { date: '2023-05-18', type: 'FLAIR sequence', status: 'Inconclusive' },
            { date: '2022-12-10', type: 'T1-Weighted', status: 'Normal' },
        ],
        diagnosisHistory: [
            { date: '2023-11-16', diagnosis: patient?.diagnosis || 'Glioma', physician: 'Dr. Silberman' },
            { date: '2023-05-20', diagnosis: 'Migraine (Chronic)', physician: 'Dr. Venkatesh' },
        ]
    };

    return (
        <div className="w-full h-full p-8 overflow-y-auto bg-[var(--bg-dark)]">
            <div className="max-w-6xl mx-auto space-y-6">

                {/* Back Button */}
                <button
                    onClick={onBack}
                    className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-main)] transition group mb-4"
                >
                    <svg className="group-hover:-translate-x-1 transition-transform" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5" /><path d="M12 19l-7-7 7-7" /></svg>
                    <span>Back to Analysis Results</span>
                </button>

                {/* Header Info */}
                <div className="flex items-end justify-between border-b border-[var(--border)] pb-6">
                    <div>
                        <div className="flex items-center gap-4 mb-2">
                            <h1 className="text-4xl font-bold text-[var(--text-main)]">Patient #{patientData.id}</h1>
                            <span className="px-3 py-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-full text-sm text-[var(--text-muted)]">
                                {patientData.gender}, {patientData.age} Years
                            </span>
                        </div>
                        <p className="text-[var(--text-muted)]">Last visit: {patientData.mriScans[0].date}</p>
                    </div>
                    <div className="flex gap-3">
                        <button className="btn bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]">Generate Full Report</button>
                        <button className="btn border border-[var(--border)] hover:bg-[var(--bg-card-hover)] text-[var(--text-main)]">Export DICOM</button>
                    </div>
                </div>

                <div className="grid grid-cols-12 gap-6">

                    {/* LEFT: MRI Gallery */}
                    <div className="col-span-8 space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-bold text-[var(--text-main)]">MRI Scan History</h2>
                            <button className="text-sm text-[var(--primary)] hover:underline">View All Scans</button>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            {patientData.mriScans.map((scan, i) => (
                                <div key={i} className="card p-4 hover:border-[var(--primary)] transition cursor-pointer group">
                                    <div className="aspect-[4/3] bg-black rounded mb-3 overflow-hidden relative">
                                        {/* Placeholder for MRI Image */}
                                        <div className="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] bg-gray-900">
                                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" /><line x1="17.5" y1="8" x2="22" y2="11" /></svg>
                                        </div>
                                        <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/70 text-white text-[10px] rounded backdrop-blur-sm">
                                            {scan.type}
                                        </div>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="font-mono text-sm text-[var(--text-muted)]">{scan.date}</span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${scan.status === 'Abnormal' ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'}`}>
                                            {scan.status}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* RIGHT: Diagnosis & Vitals */}
                    <div className="col-span-4 space-y-6">
                        <div className="card p-6">
                            <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /><path d="M16 13H8" /><path d="M16 17H8" /><path d="M10 9H8" /></svg>
                                Diagnosis Timeline
                            </h3>
                            <div className="space-y-6 relative before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-px before:bg-[var(--border)]">
                                {patientData.diagnosisHistory.map((dx, i) => (
                                    <div key={i} className="relative pl-6">
                                        <div className="absolute left-0 top-1.5 w-3 h-3 bg-[var(--primary)] rounded-full border-2 border-[var(--bg-card)]"></div>
                                        <p className="text-sm text-[var(--text-muted)] mb-1 font-mono">{dx.date}</p>
                                        <p className="font-bold text-[var(--text-main)]">{dx.diagnosis}</p>
                                        <p className="text-xs text-[var(--text-muted)]">By {dx.physician}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default PatientDetailView;
