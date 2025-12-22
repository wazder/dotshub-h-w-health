import React, { useState, useMemo } from 'react';

// Model çıktısı için çeviriler (Binary Classification: No Finding vs Mass/Nodule)
const MODEL_LABELS = {
    'No Finding': {
        tr: 'Normal - Bulgu Yok',
        description: 'Yapay zeka modeli görüntüde kitle veya nodül tespit etmedi.',
        color: 'green'
    },
    'Mass|Nodule': {
        tr: 'Patoloji Tespit Edildi',
        description: 'Yapay zeka modeli görüntüde kitle veya nodül şüphesi tespit etti. Uzman değerlendirmesi önerilir.',
        color: 'red'
    },
    'Pathology': {
        tr: 'Patoloji Tespit Edildi',
        description: 'Yapay zeka modeli görüntüde kitle veya nodül şüphesi tespit etti.',
        color: 'red'
    },
    'Error': {
        tr: 'Analiz Hatası',
        description: 'Görüntü analiz edilemedi.',
        color: 'yellow'
    }
};

// Dataset'teki tanılar için çeviriler (benzer vakalarda gösterilir)
const DIAGNOSIS_TERMS = {
    'No Finding': 'Bulgu Yok',
    'Nodule': 'Nodül',
    'Mass': 'Kitle',
    'Mass|Nodule': 'Kitle/Nodül',
    'Infiltration': 'İnfiltrasyon',
    'Atelectasis': 'Atelektazi',
    'Effusion': 'Efüzyon',
    'Pneumothorax': 'Pnömotoraks',
    'Consolidation': 'Konsolidasyon',
    'Pleural_Thickening': 'Plevral Kalınlaşma',
    'Cardiomegaly': 'Kardiyomegali',
    'Emphysema': 'Amfizem',
    'Edema': 'Ödem',
    'Fibrosis': 'Fibrozis',
    'Pneumonia': 'Pnömoni',
    'Hernia': 'Herni'
};

const translateDiagnosis = (term) => {
    if (!term) return 'Bilgi Yok';
    return DIAGNOSIS_TERMS[term] || term;
};

const getModelLabel = (label) => {
    return MODEL_LABELS[label] || MODEL_LABELS['No Finding'];
};

const ResultsView = ({ image, onSelectPatient, analysisResult, uploadedFileName }) => {
    const [visibleCount, setVisibleCount] = useState(3);

    // API sonucundan verileri çıkar
    const { aiDiagnosis, matches } = useMemo(() => {
        if (!analysisResult) {
            // API sonucu yoksa boş döndür - mock data kullanmıyoruz
            return {
                aiDiagnosis: { label: 'Error', probability: 0, confidence: 'Yok', isPathology: false },
                matches: []
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
                diagnosis: history.diagnosis || 'Bilgi Yok',
                age: history.age || 0,
                gender: history.gender || null,
                imageId: sc.imageId,
                imageUrl: sc.imageUrl
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
                diagnosis: history.diagnosis || 'Bilgi Yok',
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
                confidence: aiAnalysis.confidence || 'Bilinmiyor',
                isPathology: aiAnalysis.isPathology || false
            },
            matches: matchList
        };
    }, [analysisResult]);

    const handleExpand = () => {
        setVisibleCount(prev => Math.min(prev + 3, matches.length));
    };

    // Dosya tipini belirle
    const getFileType = () => {
        if (uploadedFileName) {
            const ext = uploadedFileName.split('.').pop()?.toLowerCase();
            if (ext === 'dcm' || ext === 'dicom') return 'DICOM Görüntüsü';
            if (ext === 'png') return 'PNG Görüntüsü';
            if (ext === 'jpg' || ext === 'jpeg') return 'JPEG Görüntüsü';
            if (ext === 'nii' || ext === 'gz') return 'NIfTI Görüntüsü';
            return `${ext?.toUpperCase()} Dosyası`;
        }
        return 'Göğüs Röntgeni';
    };

    // Model sonucu için bilgi al
    const modelInfo = getModelLabel(aiDiagnosis.label);
    const isPathology = aiDiagnosis.isPathology || aiDiagnosis.label === 'Mass|Nodule' || aiDiagnosis.label === 'Pathology';

    return (
        <div className="w-full h-full grid grid-cols-12 overflow-hidden">

            {/* LEFT: Current Patient (Uploaded Image) */}
            <div className="col-span-6 bg-black flex items-center justify-center relative border-r border-[var(--border)]">
                {image ? (
                    <img src={image} alt="Yüklenen Analiz" className="max-h-full max-w-full object-contain" />
                ) : (
                    <div className="text-[var(--text-muted)]">Görüntü yüklenmedi</div>
                )}

                {/* Overlay Metadata */}
                <div className="absolute top-4 left-4 bg-black/70 backdrop-blur px-3 py-1.5 rounded border border-white/10">
                    <h3 className="text-white text-sm font-bold">Yüklenen Görüntü</h3>
                    <p className="text-[var(--text-muted)] text-xs">{getFileType()}</p>
                </div>

                {/* AI Diagnosis Badge - Dürüst Model Sonucu */}
                <div className={`absolute bottom-6 left-1/2 -translate-x-1/2 backdrop-blur px-6 py-3 rounded-lg border shadow-2xl ${
                    isPathology 
                        ? 'bg-red-900/90 border-red-500 shadow-red-500/20' 
                        : 'bg-green-900/90 border-green-500 shadow-green-500/20'
                }`}>
                    <div className="text-center">
                        <span className={`font-bold text-lg ${isPathology ? 'text-red-200' : 'text-green-200'}`}>
                            {isPathology ? '⚠️ Patoloji Tespit Edildi' : '✓ Normal - Bulgu Yok'}
                        </span>
                        <div className="text-xs text-white/70 mt-1">
                            {modelInfo.description}
                        </div>
                        <div className="text-xs text-white/50 mt-2 max-w-xs">
                            ⓘ Bu model sadece ikili sınıflandırma yapar (normal/anormal). Kesin tanı için uzman değerlendirmesi gereklidir.
                        </div>
                    </div>
                </div>
            </div>

            {/* RIGHT: Related Matches List */}
            <div className="col-span-6 bg-[var(--bg-card)] flex flex-col h-full overflow-hidden">
                <div className="p-6 border-b border-[var(--border)] shrink-0">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <span className="text-[var(--success)]">●</span>
                        Benzer Vakalar
                    </h2>
                    <p className="text-sm text-[var(--text-muted)] mt-1">
                        Yapay zeka, yüklenen görüntüye benzer {matches.length} vaka buldu.
                    </p>
                    {/* Summary from Backend - More Professional */}
                    {matches.length > 0 && (
                        <div className="text-xs text-[var(--text-muted)] mt-3 bg-[var(--bg-dark)] p-3 rounded border border-[var(--border)]">
                            <div className="flex items-center gap-2 mb-1">
                                <span className="text-[var(--success)]">✓</span>
                                <span className="font-medium text-[var(--text-main)]">Analiz Tamamlandı</span>
                            </div>
                            <p>En yakın eşleşme: <span className="text-[var(--primary)]">Hasta #{matches[0]?.patientId}</span> (%{matches[0]?.similarity} benzerlik)</p>
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
                            {/* Match Image - Gerçek görüntü veya placeholder */}
                            <div className="w-24 h-24 bg-[var(--bg-dark)] rounded overflow-hidden relative shrink-0">
                                {match.imageUrl ? (
                                    <img 
                                        src={match.imageUrl}
                                        alt={`Hasta ${match.patientId} taraması`}
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
                                    <h4 className="font-bold text-lg text-white">Hasta #{match.id}</h4>
                                    <span className="text-[var(--success)] font-mono font-bold bg-[var(--success)]/10 px-2 py-0.5 rounded text-sm">
                                        %{match.similarity} Benzerlik
                                    </span>
                                </div>
                                <p className="text-[var(--primary)] text-sm mb-2 font-medium">{translateDiagnosis(match.diagnosis)}</p>

                                <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                                    {match.age > 0 && (
                                        <span className="bg-[var(--bg-dark)] px-2 py-1 rounded">Yaş: {match.age}</span>
                                    )}
                                    {match.gender && match.gender !== 'Bilinmiyor' && match.gender !== 'Unknown' && (
                                        <span className="bg-[var(--bg-dark)] px-2 py-1 rounded">
                                            {match.gender === 'F' || match.gender === 'Kadın' ? 'Kadın' : 
                                             match.gender === 'M' || match.gender === 'Erkek' ? 'Erkek' : match.gender}
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
                            3 Vaka Daha Göster
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ResultsView;
