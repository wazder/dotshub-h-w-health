import React, { useState, useEffect } from 'react';

const PatientDetailView = ({ patient, onBack }) => {
    const [patientData, setPatientData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Hasta ID'sini al
    const patientId = patient?.patientId || patient?.id?.replace('PT-', '') || 'Unknown';

    useEffect(() => {
        const fetchPatientData = async () => {
            try {
                setLoading(true);
                const response = await fetch(`/api/patients/${patientId}`);
                
                if (response.ok) {
                    const data = await response.json();
                    setPatientData(data.patient);
                } else {
                    // API'den veri gelmezse prop'lardan oluştur
                    setPatientData(null);
                }
            } catch (err) {
                console.error('Patient fetch error:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (patientId && patientId !== 'Unknown') {
            fetchPatientData();
        } else {
            setLoading(false);
        }
    }, [patientId]);

    // Gösterilecek verileri birleştir
    const displayData = {
        id: patientId,
        age: patientData?.age || patient?.age || 45,
        gender: patientData?.gender || patient?.gender || 'Bilinmiyor',
        diagnosis: patientData?.diagnosis || patient?.diagnosis || 'Bilinmiyor',
        scans: patientData?.scans || [],
        diagnosisHistory: patientData?.diagnosisHistory || [
            { date: '2023-11-16', diagnosis: patient?.diagnosis || 'Bilinmiyor', physician: 'Dr. AI System' }
        ],
        allFindings: patientData?.all_findings || [],
        imageCount: patientData?.image_count || 0
    };

    if (loading) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-[var(--bg-dark)]">
                <div className="text-center">
                    <div className="animate-spin w-12 h-12 border-4 border-[var(--primary)] border-t-transparent rounded-full mx-auto mb-4"></div>
                    <p className="text-[var(--text-muted)]">Hasta bilgileri yükleniyor...</p>
                </div>
            </div>
        );
    }

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
                            <h1 className="text-4xl font-bold text-[var(--text-main)]">Patient #PT-{displayData.id}</h1>
                            <span className="px-3 py-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-full text-sm text-[var(--text-muted)]">
                                {displayData.gender}, {displayData.age} Years
                            </span>
                        </div>
                        <p className="text-[var(--text-muted)]">
                            Last visit: {displayData.scans[0]?.date || '2023-11-15'}
                            {displayData.imageCount > 0 && ` • ${displayData.imageCount} tarama`}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button className="btn bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]">Generate Full Report</button>
                        <button className="btn border border-[var(--border)] hover:bg-[var(--bg-card-hover)] text-[var(--text-main)]">Export DICOM</button>
                    </div>
                </div>

                <div className="grid grid-cols-12 gap-6">

                    {/* LEFT: Scan Gallery */}
                    <div className="col-span-8 space-y-6">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-bold text-[var(--text-main)]">X-Ray Scan History</h2>
                            {displayData.scans.length > 4 && (
                                <button className="text-sm text-[var(--primary)] hover:underline">View All Scans</button>
                            )}
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            {displayData.scans.length > 0 ? (
                                displayData.scans.slice(0, 4).map((scan, i) => (
                                    <div key={scan.id || i} className="card p-4 hover:border-[var(--primary)] transition cursor-pointer group">
                                        <div className="aspect-[4/3] bg-black rounded mb-3 overflow-hidden relative">
                                            {scan.imageUrl ? (
                                                <img 
                                                    src={scan.imageUrl}
                                                    alt={`Scan ${scan.id}`}
                                                    className="w-full h-full object-cover grayscale group-hover:scale-105 transition-transform"
                                                    onError={(e) => {
                                                        e.target.style.display = 'none';
                                                    }}
                                                />
                                            ) : (
                                                <div className="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] bg-gray-900">
                                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                                        <circle cx="8.5" cy="8.5" r="1.5"/>
                                                        <polyline points="21 15 16 10 5 21"/>
                                                    </svg>
                                                </div>
                                            )}
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
                                        {scan.findings && scan.findings !== 'No Finding' && (
                                            <p className="text-xs text-[var(--text-muted)] mt-2 truncate">{scan.findings}</p>
                                        )}
                                    </div>
                                ))
                            ) : (
                                <div className="col-span-2 card p-8 text-center text-[var(--text-muted)]">
                                    <svg className="mx-auto mb-4" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                        <circle cx="8.5" cy="8.5" r="1.5"/>
                                        <polyline points="21 15 16 10 5 21"/>
                                    </svg>
                                    <p>Bu hasta için tarama verisi bulunamadı</p>
                                </div>
                            )}
                        </div>
                        
                        {/* All Findings */}
                        {displayData.allFindings.length > 0 && (
                            <div className="card p-4">
                                <h3 className="font-bold text-[var(--text-main)] mb-3">Tüm Bulgular</h3>
                                <div className="flex flex-wrap gap-2">
                                    {displayData.allFindings.map((finding, i) => (
                                        <span 
                                            key={i} 
                                            className={`px-3 py-1 rounded-full text-sm ${
                                                finding === 'No Finding' 
                                                    ? 'bg-green-500/20 text-green-300' 
                                                    : 'bg-orange-500/20 text-orange-300'
                                            }`}
                                        >
                                            {finding}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* RIGHT: Diagnosis & Vitals */}
                    <div className="col-span-4 space-y-6">
                        <div className="card p-6">
                            <h3 className="font-bold text-[var(--text-main)] mb-4 flex items-center gap-2">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" /><path d="M16 13H8" /><path d="M16 17H8" /><path d="M10 9H8" /></svg>
                                Diagnosis Timeline
                            </h3>
                            <div className="space-y-6 relative before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-px before:bg-[var(--border)]">
                                {displayData.diagnosisHistory.map((dx, i) => (
                                    <div key={i} className="relative pl-6">
                                        <div className="absolute left-0 top-1.5 w-3 h-3 bg-[var(--primary)] rounded-full border-2 border-[var(--bg-card)]"></div>
                                        <p className="text-sm text-[var(--text-muted)] mb-1 font-mono">{dx.date}</p>
                                        <p className="font-bold text-[var(--text-main)]">{dx.diagnosis}</p>
                                        <p className="text-xs text-[var(--text-muted)]">By {dx.physician}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                        
                        {/* Primary Diagnosis Card */}
                        <div className="card p-6 bg-gradient-to-br from-[var(--primary)]/10 to-transparent border-[var(--primary)]/30">
                            <h3 className="font-bold text-[var(--text-main)] mb-2">Ana Tanı</h3>
                            <p className="text-2xl font-bold text-[var(--primary)]">{displayData.diagnosis}</p>
                            <p className="text-sm text-[var(--text-muted)] mt-2">
                                Yaş: {displayData.age} • Cinsiyet: {displayData.gender}
                            </p>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default PatientDetailView;
