import React, { useState } from 'react';
import UploadZone from './UploadZone';
import AnalysisView from './AnalysisView';
import ResultsView from './ResultsView';
import api from '../services/api';
import { useAnalysis } from '../hooks/useApi';

const Dashboard = ({ onSelectPatient }) => {
    const [step, setStep] = useState('upload'); // upload, analyzing, results
    const [currentImage, setCurrentImage] = useState(null);
    const [currentFile, setCurrentFile] = useState(null);
    
    // API entegrasyonu için hook
    const analysis = useAnalysis();

    const handleUpload = async (file) => {
        // Preview için local URL oluştur
        setCurrentImage(URL.createObjectURL(file));
        setCurrentFile(file);
        setStep('analyzing');
        
        // Gerçek API çağrısı
        const result = await analysis.analyze(file, api.analyzeImage);
        
        if (result) {
            // Başarılı analiz - results ekranına geç
            setStep('results');
        } else if (analysis.isError) {
            // Hata durumunda upload ekranına dön
            console.error('Analiz hatası:', analysis.error);
            // Kullanıcıya hata göster (opsiyonel olarak alert yerine toast kullanılabilir)
            alert(`Analiz hatası: ${analysis.error?.message || 'Bilinmeyen hata'}`);
            handleReset();
        }
    };

    const handleAnalysisComplete = () => {
        setStep('results');
    };

    const handleReset = () => {
        setStep('upload');
        setCurrentImage(null);
        setCurrentFile(null);
        analysis.reset();
    };

    return (
        <div className="w-full h-full p-6 relative">
            <div className="max-w-7xl mx-auto h-full flex flex-col">

                {/* Progress / Status Bar */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold mb-1">
                            {step === 'upload' && 'Yeni Görüntü Yükle'}
                            {step === 'analyzing' && 'Analiz Ediliyor'}
                            {step === 'results' && 'Klinik Karar Desteği'}
                        </h1>
                        <p className="text-sm text-[var(--text-muted)]">
                            {step === 'upload' && 'Analiz için röntgen veya DICOM görüntüsü yükleyin.'}
                            {step === 'analyzing' && (analysis.statusMessage || 'Görüntü analiz ediliyor, lütfen bekleyin...')}
                            {step === 'results' && 'Benzer vakalar yapay zeka ile eşleştirildi.'}
                        </p>
                    </div>

                    {step !== 'upload' && (
                        <div className="flex gap-2">
                            <button onClick={handleReset} className="btn text-sm text-[var(--text-muted)] hover:text-white border border-[var(--border)]">
                                Yeni Arama
                            </button>
                        </div>
                    )}
                </div>

                {/* Main Viewport */}
                <div className="flex-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-xl relative overflow-hidden shadow-2xl">
                    {step === 'upload' && <UploadZone onUpload={handleUpload} />}
                    {step === 'analyzing' && (
                        <AnalysisView 
                            image={currentImage} 
                            onComplete={handleAnalysisComplete}
                            progress={analysis.progress}
                            status={analysis.statusMessage}
                            isRealApi={true}
                        />
                    )}
                    {step === 'results' && currentImage && (
                        <ResultsView 
                            image={currentImage} 
                            onSelectPatient={onSelectPatient}
                            analysisResult={analysis.result}
                            uploadedFileName={currentFile?.name}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
