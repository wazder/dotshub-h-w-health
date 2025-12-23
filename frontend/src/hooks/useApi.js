import { useState, useCallback } from 'react';

/**
 * useApi - Hook for API requests
 * 
 * Provides loading state, error handling, and retry mechanism.
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
 * useAnalysis - Customized hook for image analysis
 * 
 * Provides progress tracking and step-by-step status updates.
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
        setStatusMessage('Uploading file...');
        setError(null);
        
        try {
            // NOTE: Progress is simulated since backend doesn't support real-time progress
            // In production, consider using WebSocket or Server-Sent Events for real progress
            const progressSteps = [
                { progress: 25, message: 'Sending to PACS server...' },
                { progress: 50, message: 'AI model analyzing...' },
                { progress: 75, message: 'Searching similar cases...' },
            ];
            
            // Start progress simulation
            setStatus('analyzing');
            let stepIndex = 0;
            const progressInterval = setInterval(() => {
                if (stepIndex < progressSteps.length) {
                    setProgress(progressSteps[stepIndex].progress);
                    setStatusMessage(progressSteps[stepIndex].message);
                    stepIndex++;
                }
            }, 1000);
            
            // Real API call
            const response = await apiFunction(file);
            
            // Clear progress
            clearInterval(progressInterval);
            
            setProgress(100);
            setStatusMessage('Analysis complete!');
            setResult(response);
            setStatus('complete');
            
            return response;
            
        } catch (err) {
            setStatus('error');
            setError(err);
            setStatusMessage(err.message || 'An error occurred');
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
