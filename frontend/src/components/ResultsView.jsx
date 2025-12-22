import React, { useState } from 'react';

// Mock Data Generator
const MOCK_MATCHES = Array.from({ length: 12 }, (_, i) => ({
    id: `PT-${1000 + i}`,
    similarity: (98 - i * 1.5).toFixed(1),
    diagnosis: i % 2 === 0 ? 'Glioblastoma Multiforme' : 'Anaplastic Astrocytoma',
    age: 45 + (i * 3) % 40,
    date: `2023-${(i % 12) + 1}-15`,
    outcome: i % 3 === 0 ? 'Remission' : i % 3 === 1 ? 'Stable' : 'Recurrence',
    imgUrl: null // In a real app, this would be a URL. We'll use a placeholder.
}));

const ResultsView = ({ image, onSelectPatient }) => {
    const [visibleCount, setVisibleCount] = useState(3);

    const handleExpand = () => {
        setVisibleCount(prev => Math.min(prev + 3, MOCK_MATCHES.length));
    };

    return (
        <div className="w-full h-full grid grid-cols-12 overflow-hidden">

            {/* LEFT: Current Patient (Uploaded Image) */}
            <div className="col-span-6 bg-black flex items-center justify-center relative border-r border-[var(--border)]">
                {image ? (
                    <img src={image} alt="Uploaded Analysis" className="max-h-full max-w-full object-contain" />
                ) : (
                    <div className="text-[var(--text-muted)]">No image loaded</div>
                )}

                {/* Overlay Metadata */}
                <div className="absolute top-4 left-4 bg-black/70 backdrop-blur px-3 py-1.5 rounded border border-white/10">
                    <h3 className="text-white text-sm font-bold">Uploaded Scan</h3>
                    <p className="text-[var(--text-muted)] text-xs">DICOM / AXIAL</p>
                </div>

                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-[var(--primary)]/90 backdrop-blur px-6 py-2 rounded-full border border-[var(--primary)] shadow-2xl shadow-[var(--primary)]/20 animate-pulse">
                    <span className="font-bold text-white text-sm">Diagnosis: Glioblastoma (Grade IV)</span>
                </div>
            </div>

            {/* RIGHT: Related Matches List */}
            <div className="col-span-6 bg-[var(--bg-card)] flex flex-col h-full overflow-hidden">
                <div className="p-6 border-b border-[var(--border)] shrink-0">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <span className="text-[var(--success)]">●</span>
                        Similar Case Matches
                    </h2>
                    <p className="text-sm text-[var(--text-muted)] mt-1">
                        AI found {MOCK_MATCHES.length} confirmed cases with high structural similarity.
                    </p>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {MOCK_MATCHES.slice(0, visibleCount).map((match, idx) => (
                        <div
                            key={match.id}
                            onClick={() => onSelectPatient && onSelectPatient(match)}
                            className="card p-4 flex gap-4 hover:bg-[var(--bg-card-hover)] transition group border border-[var(--border)] cursor-pointer"
                        >
                            {/* Match Image Placeholder */}
                            <div className="w-24 h-24 bg-[var(--bg-dark)] rounded overflow-hidden relative shrink-0">
                                <div className="absolute inset-0 flex items-center justify-center text-[var(--text-muted)] text-xs">
                                    match_img_{idx + 1}
                                </div>
                                {/* Visual noise to simulate brain scan thumbnail */}
                                <div className="absolute inset-0 opacity-20 bg-[url('https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/Glioblastoma_MR_T1_C%2B_Tra_01.jpg/220px-Glioblastoma_MR_T1_C%2B_Tra_01.jpg')] bg-cover bg-center grayscale mix-blend-overlay"></div>
                            </div>

                            {/* Match Details */}
                            <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-start mb-1">
                                    <h4 className="font-bold text-lg text-white">Patient #{match.id}</h4>
                                    <span className="text-[var(--success)] font-mono font-bold bg-[var(--success)]/10 px-2 py-0.5 rounded text-sm">
                                        {match.similarity}% Sim
                                    </span>
                                </div>
                                <p className="text-[var(--text-muted)] text-sm mb-2">{match.diagnosis}</p>

                                <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
                                    <span className="bg-[var(--bg-dark)] px-2 py-1 rounded">Age: {match.age}</span>
                                    <span className={`px-2 py-1 rounded border ${match.outcome === 'Recurrence' ? 'border-red-900 text-red-300 bg-red-900/10' :
                                        match.outcome === 'Remission' ? 'border-green-900 text-green-300 bg-green-900/10' :
                                            'border-yellow-900 text-yellow-300 bg-yellow-900/10'
                                        }`}>
                                        {match.outcome}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Expand Button */}
                    {visibleCount < MOCK_MATCHES.length && (
                        <button
                            onClick={handleExpand}
                            className="w-full py-3 mt-4 flex items-center justify-center gap-2 text-sm font-bold text-[var(--text-muted)] hover:text-white border border-dashed border-[var(--border)] hover:border-[var(--primary)] rounded-xl transition-all hover:bg-[var(--bg-card-hover)]"
                        >
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="16"></line>
                                <line x1="8" y1="12" x2="16" y2="12"></line>
                            </svg>
                            Show 3 More Matches
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ResultsView;
