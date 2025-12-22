import React, { useState, useMemo } from 'react';

// Fallback Mock Data - API sonucu yoksa kullanılır
const MOCK_MATCHES = Array.from({ length: 12 }, (_, i) => ({
    id: `PT-${1000 + i}`,
    patientId: `${1000 + i}`,
    similarity: (98 - i * 1.5).toFixed(1),
    similarityScore: (0.98 - i * 0.015),
    diagnosis: i % 2 === 0 ? 'Glioblastoma Multiforme' : 'Anaplastic Astrocytoma',
    age: 45 + (i * 3) % 40,
    date: `2023-${(i % 12) + 1}-15`,
    outcome: i % 3 === 0 ? 'Remission' : i % 3 === 1 ? 'Stable' : 'Recurrence',
    imgUrl: null
}));

const ResultsView = ({ image, onSelectPatient, analysisResult }) => {
    const [visibleCount, setVisibleCount] = useState(3);

    // API sonucundan verileri çıkar veya fallback kullan
    const { aiDiagnosis, matches, summary } = useMemo(() => {
        if (!analysisResult) {
            return {
                aiDiagnosis: { label: 'Glioblastoma', probability: 0.92, confidence: 'Yüksek' },
                matches: MOCK_MATCHES,
                summary: 'Mock analiz sonucu'
            };
        }

        // Backend'den gelen veriyi dönüştür
        const aiAnalysis = analysisResult.aiAnalysis || {};
        
        // Birden fazla benzer vaka (yeni format)
        const similarCases = analysisResult.similarCases || [];
        
        // Benzer vakaları işle
        let matchList = similarCases.map((sc, idx) => {
            const history = sc.history || {};
            return {
                id: `PT-${sc.patientId}`,
                patientId: sc.patientId,
                similarity: (sc.similarityScore * 100).toFixed(1),
                similarityScore: sc.similarityScore,
                diagnosis: history.diagnosis || aiAnalysis.label || 'Bilinmiyor',
                age: history.age || 0,
                gender: history.gender || 'Bilinmiyor',
                date: history.diagnosisDate || 'N/A',
                outcome: history.outcome || 'Bilinmiyor',
                treatment: history.treatment || 'Bilinmiyor',
                notes: history.notes || '',
                history: history.history || '',
                imageId: sc.imageId,
                imageUrl: sc.imageUrl  // Backend'den gelen görüntü URL'i
            };
        });

        // Eski format desteği (geriye uyumluluk)
        if (matchList.length === 0 && analysisResult.similarCase) {
            const similarCase = analysisResult.similarCase;
            const history = similarCase.history || {};
            matchList.push({
                id: `PT-${similarCase.patientId}`,
                patientId: similarCase.patientId,
                similarity: (similarCase.similarityScore * 100).toFixed(1),
                similarityScore: similarCase.similarityScore,
                diagnosis: history.diagnosis || aiAnalysis.label || 'Bilinmiyor',
                age: history.age || 0,
                gender: history.gender || 'Bilinmiyor',
                date: history.diagnosisDate || 'N/A',
                outcome: history.outcome || 'Bilinmiyor',
                treatment: history.treatment || 'Bilinmiyor',
                notes: history.notes || '',
                history: history.history || '',
                imageId: similarCase.imageId,
                imageUrl: similarCase.imageUrl
            });
        }

        return {
            aiDiagnosis: {
                label: aiAnalysis.label || 'Bilinmiyor',
                labelTr: aiAnalysis.labelTr,
                probability: aiAnalysis.probability || 0,
                confidence: aiAnalysis.confidence || 'Bilinmiyor'
            },
            matches: matchList,
            summary: analysisResult.summary || ''
        };
    }, [analysisResult]);

    const handleExpand = () => {
        setVisibleCount(prev => Math.min(prev + 3, matches.length));
    };

    // Outcome için renk belirleme
    const getOutcomeStyle = (outcome) => {
        const outcomeLC = (outcome || '').toLowerCase();
        if (outcomeLC.includes('remission') || outcomeLC.includes('iyileş') || outcomeLC.includes('tam')) {
            return 'border-green-900 text-green-300 bg-green-900/10';
        }
        if (outcomeLC.includes('recurrence') || outcomeLC.includes('nüks') || outcomeLC.includes('kötü')) {
            return 'border-red-900 text-red-300 bg-red-900/10';
        }
        return 'border-yellow-900 text-yellow-300 bg-yellow-900/10';
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

                {/* AI Diagnosis Badge - Artık gerçek veriden geliyor */}
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-[var(--primary)]/90 backdrop-blur px-6 py-2 rounded-full border border-[var(--primary)] shadow-2xl shadow-[var(--primary)]/20 animate-pulse">
                    <span className="font-bold text-white text-sm">
                        Diagnosis: {aiDiagnosis.labelTr || aiDiagnosis.label} ({(aiDiagnosis.probability * 100).toFixed(0)}% - {aiDiagnosis.confidence})
                    </span>
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
                        AI found {matches.length} confirmed cases with high structural similarity.
                    </p>
                    {/* Summary from Backend */}
                    {summary && (
                        <p className="text-xs text-[var(--primary)] mt-2 bg-[var(--primary)]/10 p-2 rounded">
                            {summary}
                        </p>
                    )}
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {matches.slice(0, visibleCount).map((match, idx) => (
                        <div
                            key={match.id}
                            onClick={() => onSelectPatient && onSelectPatient(match)}
                            className="card p-4 flex gap-4 hover:bg-[var(--bg-card-hover)] transition group border border-[var(--border)] cursor-pointer"
                        >
                            {/* Match Image - Gerçek görüntü veya placeholder */}
                            <div className="w-24 h-24 bg-[var(--bg-dark)] rounded overflow-hidden relative shrink-0">
                                {match.imageUrl ? (
                                    <img 
                                        src={match.imageUrl}
                                        alt={`Patient ${match.patientId} scan`}
                                        className="w-full h-full object-cover grayscale"
                                        onError={(e) => {
                                            e.target.style.display = 'none';
                                            e.target.nextSibling.style.display = 'flex';
                                        }}
                                    />
                                ) : null}
                                <div 
                                    className={`absolute inset-0 flex items-center justify-center text-[var(--text-muted)] text-xs bg-gray-900 ${match.imageUrl ? 'hidden' : ''}`}
                                    style={{ display: match.imageUrl ? 'none' : 'flex' }}
                                >
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                        <circle cx="8.5" cy="8.5" r="1.5"/>
                                        <polyline points="21 15 16 10 5 21"/>
                                    </svg>
                                </div>
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
                                    {match.gender && (
                                        <span className="bg-[var(--bg-dark)] px-2 py-1 rounded">{match.gender}</span>
                                    )}
                                    <span className={`px-2 py-1 rounded border ${getOutcomeStyle(match.outcome)}`}>
                                        {match.outcome}
                                    </span>
                                </div>
                                {/* Treatment info if available */}
                                {match.treatment && (
                                    <p className="text-xs text-[var(--primary)] mt-2">💊 {match.treatment}</p>
                                )}
                            </div>
                        </div>
                    ))}

                    {/* Expand Button */}
                    {visibleCount < matches.length && (
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
