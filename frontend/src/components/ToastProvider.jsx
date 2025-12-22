import React, { createContext, useContext, useState, useCallback } from 'react';

/**
 * Toast Notification Context
 * 
 * Global toast mesajları için context provider.
 * Kullanım: const { showToast } = useToast();
 */

const ToastContext = createContext(null);

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }
    return context;
};

// Toast tipleri için stiller
const TOAST_STYLES = {
    success: {
        bg: 'bg-green-500/90',
        border: 'border-green-400',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        )
    },
    error: {
        bg: 'bg-red-500/90',
        border: 'border-red-400',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
        )
    },
    warning: {
        bg: 'bg-yellow-500/90',
        border: 'border-yellow-400',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
        )
    },
    info: {
        bg: 'bg-blue-500/90',
        border: 'border-blue-400',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
        )
    }
};

/**
 * Toast Component
 */
const Toast = ({ id, type = 'info', message, onClose }) => {
    const style = TOAST_STYLES[type] || TOAST_STYLES.info;
    
    return (
        <div 
            className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border ${style.bg} ${style.border} text-white backdrop-blur-sm animate-in slide-in-from-right duration-300`}
            role="alert"
        >
            <span className="shrink-0">{style.icon}</span>
            <p className="text-sm font-medium flex-1">{message}</p>
            <button 
                onClick={() => onClose(id)}
                className="shrink-0 hover:opacity-70 transition"
            >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
    );
};

/**
 * Toast Provider Component
 */
export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);
    
    const showToast = useCallback((type, message, duration = 5000) => {
        const id = Date.now() + Math.random();
        
        setToasts(prev => [...prev, { id, type, message }]);
        
        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => {
                removeToast(id);
            }, duration);
        }
        
        return id;
    }, []);
    
    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);
    
    // Convenience methods
    const success = useCallback((message, duration) => showToast('success', message, duration), [showToast]);
    const error = useCallback((message, duration) => showToast('error', message, duration), [showToast]);
    const warning = useCallback((message, duration) => showToast('warning', message, duration), [showToast]);
    const info = useCallback((message, duration) => showToast('info', message, duration), [showToast]);
    
    return (
        <ToastContext.Provider value={{ showToast, success, error, warning, info, removeToast }}>
            {children}
            
            {/* Toast Container */}
            <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm">
                {toasts.map(toast => (
                    <Toast 
                        key={toast.id}
                        {...toast}
                        onClose={removeToast}
                    />
                ))}
            </div>
        </ToastContext.Provider>
    );
};

export default ToastProvider;
