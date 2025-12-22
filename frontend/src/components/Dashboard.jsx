import React, { useState } from 'react';
import UploadZone from './UploadZone';
import AnalysisView from './AnalysisView';
import ResultsView from './ResultsView';

const Dashboard = ({ onSelectPatient }) => {
    const [step, setStep] = useState('upload'); // upload, analyzing, results
    const [currentImage, setCurrentImage] = useState(null);

    const handleUpload = (file) => {
        // Mock upload handling
        setCurrentImage(URL.createObjectURL(file));
        setStep('analyzing');
    };

    const handleAnalysisComplete = () => {
        setStep('results');
    };

    const handleReset = () => {
        setStep('upload');
        setCurrentImage(null);
    };

    return (
        <div className="w-full h-full p-6 relative">
            <div className="max-w-7xl mx-auto h-full flex flex-col">

                {/* Progress / Status Bar */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold mb-1">
                            {step === 'upload' && 'New Patient Entry'}
                            {step === 'analyzing' && 'Processing Analysis'}
                            {step === 'results' && 'Clinical Decision Support'}
                        </h1>
                        <p className="text-sm text-[var(--text-muted)]">
                            {step === 'upload' && 'Upload DICOM/MRI data to begin triage.'}
                            {step === 'analyzing' && 'Extracting features and searching vector database...'}
                            {step === 'results' && 'Matched similar cases based on latent space embedding.'}
                        </p>
                    </div>

                    {step !== 'upload' && (
                        <div className="flex gap-2">
                            <button onClick={handleReset} className="btn text-sm text-[var(--text-muted)] hover:text-white border border-[var(--border)]">
                                New Search
                            </button>
                        </div>
                    )}
                </div>

                {/* Main Viewport */}
                <div className="flex-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-xl relative overflow-hidden shadow-2xl">
                    {step === 'upload' && <UploadZone onUpload={handleUpload} />}
                    {step === 'analyzing' && <AnalysisView image={currentImage} onComplete={handleAnalysisComplete} />}
                    {step === 'results' && currentImage && <ResultsView image={currentImage} onSelectPatient={onSelectPatient} />}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
