import React, { useState, useMemo } from 'react';

// Disease labels for multi-label model output (14 diseases)
const DISEASE_LABELS = {
    'Atelectasis': { tr: 'Atelectasis', desc: 'Partial collapse of lung tissue' },
    'Cardiomegaly': { tr: 'Cardiomegaly', desc: 'Enlarged heart' },
    'Effusion': { tr: 'Pleural Effusion', desc: 'Fluid between lung membranes' },
    'Infiltration': { tr: 'Infiltration', desc: 'Fluid/cell accumulation in lung tissue' },
    'Mass': { tr: 'Mass', desc: 'Large lesion in lung' },
    'Nodule': { tr: 'Nodule', desc: 'Small round lesion in lung' },
    'Pneumonia': { tr: 'Pneumonia', desc: 'Lung infection' },
    'Pneumothorax': { tr: 'Pneumothorax', desc: 'Air between lung and chest wall - URGENT!' },
    'Consolidation': { tr: 'Consolidation', desc: 'Densification of lung tissue' },
    'Edema': { tr: 'Pulmonary Edema', desc: 'Fluid accumulation in lungs' },
    'Emphysema': { tr: 'Emphysema', desc: 'Damage to air sacs (COPD)' },
    'Fibrosis': { tr: 'Fibrosis', desc: 'Scarring of lung tissue' },
    'Pleural_Thickening': { tr: 'Pleural Thickening', desc: 'Thickening of lung membrane' },
    'Hernia': { tr: 'Hernia', desc: 'Diaphragmatic hernia' },
    'No Finding': { tr: 'Normal - No Finding', desc: 'No pathology detected' }
};

const translateDiagnosis = (term) => {
    if (!term) return 'No Information';
    const disease = DISEASE_LABELS[term];
    return disease ? disease.tr : term;
};

const getDiseaseInfo = (label) => {
    return DISEASE_LABELS[label] || { tr: label, desc: '' };
};

const ResultsView = ({ image, onSelectPatient, analysisResult, uploadedFileName }) => {
    const [visibleCount, setVisibleCount] = useState(3);

    // Extract data from API result
    const { aiDiagnosis, matches } = useMemo(() => {
        if (!analysisResult) {
            // Return empty if no API result - not using mock data
            return {
                aiDiagnosis: { label: 'Error', probability: 0, confidence: 'None', isPathology: false },
                matches: []
            };
        }

        // Transform data from backend
        const aiAnalysis = analysisResult.aiAnalysis || {};
        
        // Multiple similar cases (new format)
        const similarCases = analysisResult.similarCases || {};
        
        // Process similar cases
        let matchList = similarCases.map((sc, idx) => {
            const history = sc.history || {};
            return {
                id: `PT-${sc.patientId}`,
                patientId: sc.patientId,
                similarity: (sc.similarityScore * 100).toFixed(1),
                similarityScore: sc.similarityScore,
                diagnosis: history.diagnosis || 'No Information',
                age: history.age || 0,
                gender: history.gender || null,
                imageId: sc.imageId,
                imageUrl: sc.imageUrl
            };
        });

        // Old format support (backward compatibility)
        if (matchList.length === 0 && analysisResult.similarCase) {
            const similarCase = analysisResult.similarCase;
            const history = similarCase.history || {};
            matchList.push({
                id: `PT-${similarCase.patientId}`,
                patientId: similarCase.patientId,
                similarity: (similarCase.similarityScore * 100).toFixed(1),
                similarityScore: similarCase.similarityScore,
                diagnosis: history.diagnosis || 'No Information',
                age: history.age || 0,
                gender: history.gender || null,
                imageId: similarCase.imageId,
                imageUrl: similarCase.imageUrl
            });
        }

        return {
            aiDiagnosis: {
                label: aiAnalysis.label || 'Error',
                labelTr: aiAnalysis.labelTr,
                probability: aiAnalysis.probability || 0,
                confidence: aiAnalysis.confidence || 'Unknown',
                isPathology: aiAnalysis.isPathology || false,
                detectedDiseases: aiAnalysis.detectedDiseases || [],
                diseaseCount: aiAnalysis.diseaseCount || 0
            },
            matches: matchList
        };
    }, [analysisResult]);

    const handleExpand = () => {
        setVisibleCount(prev => Math.min(prev + 3, matches.length));
    };

    // Determine file type
    const getFileType = () => {
        if (uploadedFileName) {
            const ext = uploadedFileName.split('.').pop()?.toLowerCase();
            if (ext === 'dcm' || ext === 'dicom') return 'DICOM Image';
            if (ext === 'png') return 'PNG Image';
            if (ext === 'jpg' || ext === 'jpeg') return 'JPEG Image';
            if (ext === 'nii' || ext === 'gz') return 'NIfTI Image';
            return `${ext?.toUpperCase()} File`;
        }
        return 'Chest X-Ray';
    };

    // Multi-label results
    const isPathology = aiDiagnosis.isPathology;
    const detectedDiseases = aiDiagnosis.detectedDiseases || [];

    return (
        <div className="w-full h-full grid grid-cols-12 overflow-hidden">

            {/* LEFT: Current Patient (Uploaded Image) */}
            <div className="col-span-6 bg-black flex items-center justify-center relative border-r border-[var(--border)]">
                {image ? (
                    <img src={image} alt="Uploaded Analysis" className="max-h-full max-w-full object-contain" />
                ) : (
                    <div className="text-[var(--text-muted)]">No image uploaded</div>
                )}

                {/* Overlay Metadata */}
                <div className="absolute top-4 left-4 bg-black/70 backdrop-blur px-3 py-1.5 rounded border border-white/10">
                    <h3 className="text-white text-sm font-bold">Uploaded Image</h3>
                    <p className="text-[var(--text-muted)] text-xs">{getFileType()}</p>
                </div>

                {/* AI Diagnosis Badge - Multi-Label Model Result */}
                <div className={`absolute bottom-6 left-1/2 -translate-x-1/2 backdrop-blur px-6 py-4 rounded-lg border shadow-2xl max-w-md ${
                    isPathology 
                        ? 'bg-red-900/90 border-red-500 shadow-red-500/20' 
                        : 'bg-green-900/90 border-green-500 shadow-green-500/20'
                }`}>
                    <div className="text-center">
                        <span className={`font-bold text-lg ${isPathology ? 'text-red-200' : 'text-green-200'}`}>
                            {isPathology 
                                ? `⚠️ ${detectedDiseases.length} Pathology Detected` 
                                : '✓ Normal - No Finding'}
                        </span>
                        
                        {/* Detected diseases list */}
                        {isPathology && detectedDiseases.length > 0 && (
                            <div className="mt-3 space-y-1 text-left">
                                {detectedDiseases.slice(0, 3).map((disease, idx) => (
                                    <div key={idx} className="flex items-center justify-between bg-black/30 px-3 py-1.5 rounded">
                                        <span className="text-white text-sm">{disease.labelTr || disease.label}</span>
                                        <span className="text-red-300 text-xs font-mono">%{(disease.probability * 100).toFixed(0)}</span>
                                    </div>
                                ))}
                                {detectedDiseases.length > 3 && (
                                    <p className="text-white/50 text-xs text-center">+{detectedDiseases.length - 3} more findings</p>
                                )}
                            </div>
                        )}
                        
                        <div className="text-xs text-white/50 mt-3">
                            ⓘ This model can detect 14 different lung pathologies. Expert evaluation is required for definitive diagnosis.
                        </div>
                    </div>
                </div>
            </div>

            {/* RIGHT: Related Matches List */}
            <div className="col-span-6 bg-[var(--bg-card)] flex flex-col h-full overflow-hidden">
                <div className="p-6 border-b border-[var(--border)] shrink-0">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <span className="text-[var(--success)]">●</span>
                        Similar Cases
                    </h2>
                    <p className="text-sm text-[var(--text-muted)] mt-1">
                        AI found {matches.length} similar cases to the uploaded image.
                    </p>
                    {/* Summary from Backend - More Professional */}
                    {matches.length > 0 && (
                        <div className="text-xs text-[var(--text-muted)] mt-3 bg-[var(--bg-dark)] p-3 rounded border border-[var(--border)]">
                            <div className="flex items-center gap-2 mb-1">
                                <span className="text-[var(--success)]">✓</span>
                                <span className="font-medium text-[var(--text-main)]">Analysis Complete</span>
                            </div>
                            <p>Closest match: <span className="text-[var(--primary)]">Patient #{matches[0]?.patientId}</span> ({matches[0]?.similarity}% similarity)</p>
                        </div>
                    )}
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {matches.slice(0, visibleCount).map((match, idx) => (
                        <div
                            key={match.id}
                            onClick={() => onSelectPatient && onSelectPatient(match)}
                            className="card p-4 flex gap-4 hover:bg-[var(--bg-card-hover)] transition group border border-[var(--border)] cursor-pointer"
                        >
                            {/* Match Image - Real image or placeholder */}
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
                                        {match.similarity}% Similarity
                                    </span>
                                </div>
                                <p className="text-[var(--primary)] text-sm mb-2 font-medium">{translateDiagnosis(match.diagnosis)}</p>

                                <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                                    {match.age > 0 && (
                                        <span className="bg-[var(--bg-dark)] px-2 py-1 rounded">Age: {match.age}</span>
                                    )}
                                    {match.gender && match.gender !== 'Unknown' && (
                                        <span className="bg-[var(--bg-dark)] px-2 py-1 rounded">
                                            {match.gender === 'F' || match.gender === 'Female' ? 'Female' : 
                                             match.gender === 'M' || match.gender === 'Male' ? 'Male' : match.gender}
                                        </span>
                                    )}
                                </div>
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
                            Show 3 More Cases
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ResultsView;
