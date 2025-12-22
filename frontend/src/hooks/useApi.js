import { useState, useCallback } from 'react';

/**
 * useApi - API istekleri için hook
 * 
 * Loading state, error handling ve retry mekanizması sağlar.
 * 
 * @example
 * const { data, error, loading, execute } = useApi(api.analyzeImage);
 * 
 * const handleUpload = async (file) => {
 *   const result = await execute(file);
 *   if (result) {
 *     // Success
 *   }
 * };
 */
export function useApi(apiFunction) {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const execute = useCallback(async (...args) => {
        setLoading(true);
        setError(null);
        
        try {
            const result = await apiFunction(...args);
            setData(result);
            return result;
        } catch (err) {
            setError(err);
            return null;
        } finally {
            setLoading(false);
        }
    }, [apiFunction]);
    
    const reset = useCallback(() => {
        setData(null);
        setError(null);
        setLoading(false);
    }, []);
    
    return { data, error, loading, execute, reset };
}

/**
 * useAnalysis - Görüntü analizi için özelleştirilmiş hook
 * 
 * Progress tracking ve step-by-step status updates sağlar.
 */
export function useAnalysis() {
    const [status, setStatus] = useState('idle'); // idle, uploading, analyzing, complete, error
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    
    const analyze = useCallback(async (file, apiFunction) => {
        setStatus('uploading');
        setProgress(10);
        setStatusMessage('Dosya yükleniyor...');
        setError(null);
        
        try {
            // Simüle edilmiş progress (gerçek API progress tracking desteklemiyorsa)
            const progressSteps = [
                { progress: 25, message: 'PACS sunucusuna gönderiliyor...' },
                { progress: 50, message: 'AI modeli analiz yapıyor...' },
                { progress: 75, message: 'Benzer vakalar aranıyor...' },
            ];
            
            // Progress simulation başlat
            setStatus('analyzing');
            let stepIndex = 0;
            const progressInterval = setInterval(() => {
                if (stepIndex < progressSteps.length) {
                    setProgress(progressSteps[stepIndex].progress);
                    setStatusMessage(progressSteps[stepIndex].message);
                    stepIndex++;
                }
            }, 1000);
            
            // Gerçek API çağrısı
            const response = await apiFunction(file);
            
            // Progress temizle
            clearInterval(progressInterval);
            
            setProgress(100);
            setStatusMessage('Analiz tamamlandı!');
            setResult(response);
            setStatus('complete');
            
            return response;
            
        } catch (err) {
            setStatus('error');
            setError(err);
            setStatusMessage(err.message || 'Bir hata oluştu');
            return null;
        }
    }, []);
    
    const reset = useCallback(() => {
        setStatus('idle');
        setProgress(0);
        setStatusMessage('');
        setResult(null);
        setError(null);
    }, []);
    
    return {
        status,
        progress,
        statusMessage,
        result,
        error,
        analyze,
        reset,
        isLoading: status === 'uploading' || status === 'analyzing',
        isComplete: status === 'complete',
        isError: status === 'error'
    };
}

export default { useApi, useAnalysis };
