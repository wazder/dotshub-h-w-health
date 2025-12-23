/**
 * API Service - Backend communication layer
 * 
 * This module manages all HTTP requests centrally.
 * - Automatic error handling
 * - snake_case → camelCase conversion
 * - Token management (JWT ready)
 * - Timeout management
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000;

// ==================== Utility Functions ====================

/**
 * Converts snake_case to camelCase
 * @param {string} str - snake_case string
 * @returns {string} camelCase string
 */
const toCamelCase = (str) => {
    return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
};

/**
 * Converts camelCase to snake_case
 * @param {string} str - camelCase string
 * @returns {string} snake_case string
 */
const toSnakeCase = (str) => {
    return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
};

/**
 * Transforms object keys (deep)
 * @param {Object} obj - Object to transform
 * @param {Function} transformer - Key transformer function
 * @returns {Object} Transformed object
 */
const transformKeys = (obj, transformer) => {
    if (obj === null || obj === undefined) {
        return obj;
    }
    
    if (Array.isArray(obj)) {
        return obj.map(item => transformKeys(item, transformer));
    }
    
    if (typeof obj === 'object' && !(obj instanceof Date)) {
        return Object.keys(obj).reduce((acc, key) => {
            acc[transformer(key)] = transformKeys(obj[key], transformer);
            return acc;
        }, {});
    }
    
    return obj;
};

/**
 * Transforms backend response to frontend format
 */
export const fromBackend = (data) => transformKeys(data, toCamelCase);

/**
 * Transforms frontend data to backend format
 */
export const toBackend = (data) => transformKeys(data, toSnakeCase);

// ==================== Error Classes ====================

/**
 * API error class
 */
export class ApiError extends Error {
    constructor(message, status, code, details = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.code = code;
        this.details = details;
    }
}

/**
 * Network error class
 */
export class NetworkError extends Error {
    constructor(message = 'Network connection error') {
        super(message);
        this.name = 'NetworkError';
    }
}

/**
 * Timeout error class
 */
export class TimeoutError extends Error {
    constructor(message = 'Request timed out') {
        super(message);
        this.name = 'TimeoutError';
    }
}

// ==================== API Client ====================

/**
 * Fetch wrapper with timeout
 */
const fetchWithTimeout = async (url, options, timeout = API_TIMEOUT) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        return response;
    } finally {
        clearTimeout(timeoutId);
    }
};

/**
 * Makes API request and processes the result
 * @param {string} endpoint - API endpoint (with leading /)
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} API response (in camelCase format)
 */
const request = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Default headers
    const headers = {
        ...options.headers
    };
    
    // Add Content-Type for JSON body
    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(toBackend(options.body));
    }
    
    // Add JWT Token if available (from localStorage)
    const token = localStorage.getItem('authToken');
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
        const response = await fetchWithTimeout(url, {
            ...options,
            headers
        });
        
        // Response JSON parse
        let data;
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
            data = fromBackend(data);
        } else {
            data = await response.text();
        }
        
        // HTTP error check
        if (!response.ok) {
            throw new ApiError(
                data.message || data.detail || 'An error occurred',
                response.status,
                data.errorCode || 'UNKNOWN_ERROR',
                data.details
            );
        }
        
        return data;
        
    } catch (error) {
        // Abort (timeout)
        if (error.name === 'AbortError') {
            throw new TimeoutError();
        }
        
        // Network error
        if (error instanceof TypeError && error.message === 'Failed to fetch') {
            throw new NetworkError('Could not connect to backend server. Make sure the server is running.');
        }
        
        // ApiError already in correct format
        if (error instanceof ApiError) {
            throw error;
        }
        
        // Other errors
        throw new ApiError(error.message, 0, 'CLIENT_ERROR');
    }
};

// ==================== API Methods ====================

/**
 * GET request
 */
export const get = (endpoint, params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            searchParams.append(toSnakeCase(key), value);
        }
    });
    
    const queryString = searchParams.toString();
    const fullEndpoint = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    return request(fullEndpoint, { method: 'GET' });
};

/**
 * POST request (JSON body)
 */
export const post = (endpoint, body = {}) => {
    return request(endpoint, {
        method: 'POST',
        body
    });
};

/**
 * POST request (FormData - for file uploads)
 */
export const postFormData = (endpoint, formData) => {
    return request(endpoint, {
        method: 'POST',
        body: formData
        // Content-Type is set automatically (with boundary)
    });
};

/**
 * PUT request
 */
export const put = (endpoint, body = {}) => {
    return request(endpoint, {
        method: 'PUT',
        body
    });
};

/**
 * DELETE request
 */
export const del = (endpoint) => {
    return request(endpoint, { method: 'DELETE' });
};

// ==================== Domain-Specific API Functions ====================

/**
 * System health check
 */
export const checkHealth = () => get('/api/health');

/**
 * Medical image analysis
 * @param {File} file - File to upload (DICOM, PNG, JPEG, etc.)
 * @returns {Promise<Object>} Analysis result
 */
export const analyzeImage = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return postFormData('/api/analyze', formData);
};

/**
 * Get patient information
 * @param {string} patientId - Patient ID
 */
export const getPatient = (patientId) => get(`/api/patients/${patientId}`);

/**
 * List all patients
 */
export const listPatients = () => get('/api/patients');

// ==================== Export Default API Object ====================

const api = {
    get,
    post,
    postFormData,
    put,
    del,
    checkHealth,
    analyzeImage,
    getPatient,
    listPatients,
    // Error classes
    ApiError,
    NetworkError,
    TimeoutError,
    // Transformers
    fromBackend,
    toBackend
};

export default api;
