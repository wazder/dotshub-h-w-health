import React, { useEffect, useState } from 'react';

const AnalysisView = ({ image, onComplete, progress: externalProgress, status: externalStatus, isRealApi = false }) => {
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState('Başlatılıyor...');

    // Eğer gerçek API kullanılıyorsa, external props'ları kullan
    const displayProgress = isRealApi ? (externalProgress || 0) : progress;
    const displayStatus = isRealApi ? (externalStatus || 'İşleniyor...') : status;

    useEffect(() => {
        // Gerçek API modunda mock timeline çalıştırma
        if (isRealApi) {
            // API'den gelen progress 100'e ulaştığında complete çağır
            if (externalProgress >= 100) {
                setTimeout(onComplete, 500);
            }
            return;
        }

        // Mock mod için simüle edilmiş timeline (fallback)
        const timeline = [
            { t: 500, p: 20, s: 'Görüntü tipi belirleniyor...' },
            { t: 1500, p: 45, s: 'Akciğer bölgesi analiz ediliyor...' },
            { t: 3000, p: 70, s: 'Yapay zeka modeli çalışıyor...' },
            { t: 4500, p: 90, s: 'Benzer vakalar aranıyor...' },
            { t: 5500, p: 100, s: 'Sonuçlar hazırlanıyor...' },
        ];

        let timeoutIds = [];

        timeline.forEach(step => {
            const id = setTimeout(() => {
                setProgress(step.p);
                setStatus(step.s);
                if (step.p === 100) {
                    setTimeout(onComplete, 800);
                }
            }, step.t);
            timeoutIds.push(id);
        });

        return () => timeoutIds.forEach(clearTimeout);
    }, [onComplete, isRealApi, externalProgress]);

    return (
        <div className="w-full h-full flex items-center justify-center relative bg-black/20">
            {/* Background Image with Blur */}
            {image && (
                <div className="absolute inset-0 opacity-10 blur-xl scale-110" style={{ backgroundImage: `url(${image})`, backgroundSize: 'cover', backgroundPosition: 'center' }}></div>
            )}

            <div className="w-full max-w-md z-10 p-8 card bg-[rgba(15,23,42,0.95)] border-2 border-[var(--primary)] backdrop-blur-3xl flex flex-col items-center text-center">

                {/* Loader Ring */}
                <div className="relative w-24 h-24 mb-6">
                    <svg className="animate-spin w-full h-full" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center font-bold text-sm">
                        %{displayProgress}
                    </div>
                </div>

                <h3 className="text-xl font-bold mb-2 animate-pulse">{displayStatus}</h3>

                {/* Visual Fake Log */}
                <div className="w-full bg-black/50 rounded p-3 text-left h-24 overflow-hidden text-xs font-mono text-[var(--success)] opacity-80 mt-4 border border-[var(--border)]">
                    {displayProgress > 10 && <div>&gt; Görüntü alındı: 512x512</div>}
                    {displayProgress > 30 && <div>&gt; Görüntü tipi: Göğüs röntgeni</div>}
                    {displayProgress > 50 && <div>&gt; Yapay zeka analizi tamamlandı</div>}
                    {displayProgress > 75 && <div>&gt; {5} benzer vaka bulundu</div>}
                    <div className="animate-pulse">_</div>
                </div>
            </div>
        </div>
    );
};

export default AnalysisView;
