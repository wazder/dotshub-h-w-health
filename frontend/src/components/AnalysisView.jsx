import React, { useEffect, useState } from 'react';

const AnalysisView = ({ image, onComplete }) => {
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState('Initializing...');

    useEffect(() => {
        const timeline = [
            { t: 500, p: 20, s: 'Triaging: Confirmed BRAIN MRI' },
            { t: 1500, p: 45, s: 'Segmenting Tumor Region...' },
            { t: 3000, p: 70, s: 'Generating Feature Embeddings (ResNet50)...' },
            { t: 4500, p: 90, s: 'Querying Vector Database (Qdrant)...' },
            { t: 5500, p: 100, s: 'Ranking Matches...' },
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
    }, [onComplete]);

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
                        {progress}%
                    </div>
                </div>

                <h3 className="text-xl font-bold mb-2 animate-pulse">{status}</h3>

                {/* Visual Fake Log */}
                <div className="w-full bg-black/50 rounded p-3 text-left h-24 overflow-hidden text-xs font-mono text-[var(--success)] opacity-80 mt-4 border border-[var(--border)]">
                    {progress > 10 && <div>&gt; Input received: 512x512 DICOM</div>}
                    {progress > 30 && <div>&gt; Triage: BRAIN [Confident: 99.8%]</div>}
                    {progress > 50 && <div>&gt; Embedding: vector[1024] generated</div>}
                    {progress > 75 && <div>&gt; Vector Search: Found 5 neighbors (dist &lt; 0.2)</div>}
                    <div className="animate-pulse">_</div>
                </div>
            </div>
        </div>
    );
};

export default AnalysisView;
