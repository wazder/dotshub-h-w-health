import React, { useState, useEffect } from 'react';
import { getPatient } from '../services/api';

// Tıbbi terim çevirileri ve açıklamaları
const MEDICAL_TERMS = {
    'No Finding': { tr: 'Bulgu Yok', desc: 'Röntgende herhangi bir anormal bulgu tespit edilmedi.' },
    'Nodule': { tr: 'Nodül', desc: 'Akciğerde küçük yuvarlak lezyon. İyi huylu veya kötü huylu olabilir, takip gerektirebilir.' },
    'Infiltration': { tr: 'İnfiltrasyon', desc: 'Akciğer dokusuna sıvı veya hücre birikimi. Enfeksiyon belirtisi olabilir.' },
    'Atelectasis': { tr: 'Atelektazi', desc: 'Akciğerin bir bölümünün çökmesi veya hava kaybetmesi.' },
    'Effusion': { tr: 'Efüzyon', desc: 'Akciğer zarları arasında sıvı birikimi (plevral efüzyon).' },
    'Pneumothorax': { tr: 'Pnömotoraks', desc: 'Akciğer ile göğüs duvarı arasında hava birikimi, acil müdahale gerektirebilir.' },
    'Mass': { tr: 'Kitle', desc: 'Akciğerde büyük lezyon. İleri tetkik gerektirir.' },
    'Consolidation': { tr: 'Konsolidasyon', desc: 'Akciğer dokusunun yoğunlaşması, genellikle zatürre belirtisi.' },
    'Pleural_Thickening': { tr: 'Plevral Kalınlaşma', desc: 'Akciğer zarının kalınlaşması.' },
    'Cardiomegaly': { tr: 'Kardiyomegali', desc: 'Kalp büyümesi, kalp yetmezliği belirtisi olabilir.' },
    'Emphysema': { tr: 'Amfizem', desc: 'Akciğer hava keseciklerinin hasar görmesi, KOAH\'ın bir türü.' },
    'Edema': { tr: 'Ödem', desc: 'Akciğerlerde sıvı birikimi.' },
    'Fibrosis': { tr: 'Fibrozis', desc: 'Akciğer dokusunun sertleşmesi ve skarlaşması.' },
    'Pneumonia': { tr: 'Zatürre', desc: 'Akciğer enfeksiyonu, tedavi gerektirir.' },
    'Hernia': { tr: 'Herni', desc: 'Diyafram fıtığı.' }
};

const translateMedicalTerm = (term) => {
    if (!term) return 'Bilgi Yok';
    const found = MEDICAL_TERMS[term];
    return found ? found.tr : term;
};

const getMedicalDescription = (term) => {
    if (!term) return null;
    const found = MEDICAL_TERMS[term];
    return found ? found.desc : null;
};

const PatientDetailView = ({ patient, onBack, returnToResults }) => {
    const [patientData, setPatientData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Hasta ID'sini al
    const patientId = patient?.patientId || patient?.id?.replace('PT-', '') || 'Unknown';

    useEffect(() => {
        const fetchPatientData = async () => {
            try {
                setLoading(true);
                const data = await getPatient(patientId);
                if (data?.patient) {
                    setPatientData(data.patient);
                } else {
                    // API'den veri gelmezse prop'lardan oluştur
                    setPatientData(null);
                }
            } catch (err) {
                // API hatası - sessizce fallback kullan
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
                    onClick={returnToResults || onBack}
                    className="flex items-center gap-2 text-[var(--text-muted)] hover:text-[var(--text-main)] transition group mb-4"
                >
                    <svg className="group-hover:-translate-x-1 transition-transform" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5" /><path d="M12 19l-7-7 7-7" /></svg>
                    <span>Analiz Sonuçlarına Dön</span>
                </button>

                {/* Prototip Uyarı Banner */}
                <div className="bg-amber-900/30 border border-amber-600/50 rounded-lg p-4 flex items-start gap-3">
                    <span className="text-amber-500 text-xl">⚠️</span>
                    <div>
                        <p className="text-amber-300 font-medium">Prototip Modu - Demo Veriler</p>
                        <p className="text-amber-500/80 text-sm">
                            Bu sistemde gerçek PACS entegrasyonu bulunmamaktadır. Görüntüler NIH Chest X-ray veri setinden alınmıştır.
                            Rapor ve DICOM dışa aktarma özellikleri aktif değildir.
                        </p>
                    </div>
                </div>

                {/* Header Info */}
                <div className="flex items-end justify-between border-b border-[var(--border)] pb-6">
                    <div>
                        <div className="flex items-center gap-4 mb-2">
                            <h1 className="text-4xl font-bold text-[var(--text-main)]">Hasta #PT-{displayData.id}</h1>
                            <span className="px-3 py-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-full text-sm text-[var(--text-muted)]">
                                {displayData.gender === 'F' || displayData.gender === 'Kadın' ? 'Kadın' : 
                                 displayData.gender === 'M' || displayData.gender === 'Erkek' ? 'Erkek' : displayData.gender}, {displayData.age} Yaş
                            </span>
                        </div>
                        <p className="text-[var(--text-muted)]">
                            Son ziyaret: {displayData.scans[0]?.date || '2023-11-15'}
                            {displayData.imageCount > 0 && ` • ${displayData.imageCount} görüntü`}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button 
                            onClick={() => alert('Rapor oluşturma özelliği henüz aktif değil.')}
                            className="btn bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]"
                        >
                            Rapor Oluştur
                        </button>
                        <button 
                            onClick={() => alert('DICOM dışa aktarma özelliği henüz aktif değil.')}
                            className="btn border border-[var(--border)] hover:bg-[var(--bg-card-hover)] text-[var(--text-main)]"
                        >
                            DICOM İndir
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-12 gap-6">

                    {/* LEFT: Scan Gallery */}
                    <div className="col-span-8 space-y-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-bold text-[var(--text-main)]">Röntgen Geçmişi</h2>
                                <p className="text-xs text-[var(--text-muted)] mt-1">Bu hastanın tüm röntgen görüntüleri ve analiz sonuçları</p>
                            </div>
                            {displayData.scans.length > 4 && (
                                <button className="text-sm text-[var(--primary)] hover:underline">Tümünü Gör</button>
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
                                                    alt={`Tarama ${scan.id}`}
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
                                            {/* Çekim türü etiketi */}
                                            <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/70 text-white text-[10px] rounded backdrop-blur-sm" title="Çekim türü: PA (Posterior-Anterior) = Arkadan öne çekim, en yaygın göğüs röntgeni pozisyonu">
                                                {scan.type}
                                            </div>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="font-mono text-sm text-[var(--text-muted)]">{scan.date}</span>
                                            {/* Normal/Anormal durumu */}
                                            <span 
                                                className={`text-xs px-2 py-0.5 rounded ${scan.status === 'Abnormal' ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'}`}
                                                title={scan.status === 'Abnormal' ? 'Bu görüntüde anormal bulgu tespit edildi' : 'Bu görüntüde anormal bulgu yok'}
                                            >
                                                {scan.status === 'Abnormal' ? 'Anormal' : 'Normal'}
                                            </span>
                                        </div>
                                        {scan.findings && scan.findings !== 'No Finding' && (
                                            <p className="text-xs text-[var(--primary)] mt-2 truncate" title={getMedicalDescription(scan.findings)}>
                                                {translateMedicalTerm(scan.findings)}
                                            </p>
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
                                    <p>Bu hasta için röntgen verisi bulunamadı</p>
                                </div>
                            )}
                        </div>
                        
                        {/* All Findings - Açıklamalı */}
                        {displayData.allFindings.length > 0 && (
                            <div className="card p-4">
                                <div className="mb-3">
                                    <h3 className="font-bold text-[var(--text-main)]">Tespit Edilen Tüm Bulgular</h3>
                                    <p className="text-xs text-[var(--text-muted)]">Bu hastanın tüm röntgenlerinde tespit edilen bulgular</p>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {displayData.allFindings.map((finding, i) => (
                                        <span 
                                            key={i} 
                                            className={`px-3 py-1 rounded-full text-sm cursor-help ${
                                                finding === 'No Finding' 
                                                    ? 'bg-green-500/20 text-green-300' 
                                                    : 'bg-orange-500/20 text-orange-300'
                                            }`}
                                            title={getMedicalDescription(finding) || 'Tıbbi bulgu'}
                                        >
                                            {translateMedicalTerm(finding)}
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
                                Tanı Geçmişi
                            </h3>
                            <p className="text-xs text-[var(--text-muted)] mb-4">Yapay zeka tarafından tespit edilen tanılar</p>
                            <div className="space-y-4 relative before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-px before:bg-[var(--border)]">
                                {displayData.diagnosisHistory.map((dx, i) => (
                                    <div key={i} className="relative pl-6">
                                        <div className="absolute left-0 top-1.5 w-3 h-3 bg-[var(--primary)] rounded-full border-2 border-[var(--bg-card)]"></div>
                                        <p className="text-xs text-[var(--text-muted)] mb-1 font-mono">{dx.date}</p>
                                        <p className="font-bold text-[var(--text-main)]">{translateMedicalTerm(dx.diagnosis)}</p>
                                        <p className="text-xs text-[var(--text-muted)]">Yapay Zeka Analizi</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                        
                        {/* Primary Diagnosis Card - Açıklamalı */}
                        <div className="card p-6 bg-gradient-to-br from-[var(--primary)]/10 to-transparent border-[var(--primary)]/30">
                            <h3 className="font-bold text-[var(--text-main)] mb-2">Ana Tanı</h3>
                            <p className="text-2xl font-bold text-[var(--primary)]">{translateMedicalTerm(displayData.diagnosis)}</p>
                            {getMedicalDescription(displayData.diagnosis) && (
                                <p className="text-xs text-[var(--text-muted)] mt-2 bg-[var(--bg-dark)] p-2 rounded">
                                    {getMedicalDescription(displayData.diagnosis)}
                                </p>
                            )}
                            <p className="text-sm text-[var(--text-muted)] mt-3">
                                Yaş: {displayData.age} • Cinsiyet: {
                                    displayData.gender === 'F' || displayData.gender === 'Kadın' ? 'Kadın' : 
                                    displayData.gender === 'M' || displayData.gender === 'Erkek' ? 'Erkek' : displayData.gender
                                }
                            </p>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default PatientDetailView;
