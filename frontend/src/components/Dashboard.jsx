import React, { useState, useEffect } from 'react';
import UploadZone from './UploadZone';
import AnalysisView from './AnalysisView';
import ResultsView from './ResultsView';
import api from '../services/api';
import { useAnalysis } from '../hooks/useApi';
import { useToast } from './ToastProvider';

const Dashboard = ({ 
    onSelectPatient, 
    step, 
    setStep, 
    currentImage, 
    setCurrentImage, 
    currentFile, 
    setCurrentFile,
    analysisResult,
    setAnalysisResult
}) => {
    const { showToast } = useToast();
    
    // API integration hook
    const analysis = useAnalysis();

    // Sync analysis result to parent state when it changes
    useEffect(() => {
        if (analysis.result) {
            setAnalysisResult(analysis.result);
        }
    }, [analysis.result, setAnalysisResult]);

    const handleUpload = async (file) => {
        // Clean up old blob URL if exists
        if (currentImage && currentImage.startsWith('blob:')) {
            URL.revokeObjectURL(currentImage);
        }
        // Create local URL for preview
        setCurrentImage(URL.createObjectURL(file));
        setCurrentFile(file);
        setStep('analyzing');
        
        // Real API call
        const result = await analysis.analyze(file, api.analyzeImage);
        
        if (result) {
            // Successful analysis - go to results screen
            setStep('results');
        } else if (analysis.isError) {
            // Error - return to upload screen and show toast
            showToast(`Analysis error: ${analysis.error?.message || 'Unknown error'}`, 'error');
            handleReset();
        }
    };

    const handleAnalysisComplete = () => {
        setStep('results');
    };

    const handleReset = () => {
        // Clean up old blob URL to prevent memory leak
        if (currentImage && currentImage.startsWith('blob:')) {
            URL.revokeObjectURL(currentImage);
        }
        setStep('upload');
        setCurrentImage(null);
        setCurrentFile(null);
        setAnalysisResult(null);
        analysis.reset();
    };

    // Use stored analysis result if available
    const displayResult = analysis.result || analysisResult;

    return (
        <div className="w-full h-full p-6 relative">
            <div className="max-w-7xl mx-auto h-full flex flex-col">

                {/* Progress / Status Bar */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold mb-1">
                            {step === 'upload' && 'Upload New Image'}
                            {step === 'analyzing' && 'Analyzing'}
                            {step === 'results' && 'Clinical Decision Support'}
                        </h1>
                        <p className="text-sm text-[var(--text-muted)]">
                            {step === 'upload' && 'Upload an X-ray or DICOM image for analysis.'}
                            {step === 'analyzing' && (analysis.statusMessage || 'Image is being analyzed, please wait...')}
                            {step === 'results' && 'Similar cases matched using artificial intelligence.'}
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
                            analysisResult={displayResult}
                            uploadedFileName={currentFile?.name}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
