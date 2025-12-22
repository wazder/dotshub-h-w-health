/**
 * API Service - Backend ile iletişim katmanı
 * 
 * Bu modül tüm HTTP isteklerini merkezi olarak yönetir.
 * - Otomatik error handling
 * - snake_case → camelCase dönüşümü
 * - Token yönetimi (JWT hazır)
 * - Timeout yönetimi
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000;

// ==================== Utility Functions ====================

/**
 * snake_case'i camelCase'e dönüştürür
 * @param {string} str - snake_case string
 * @returns {string} camelCase string
 */
const toCamelCase = (str) => {
    return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
};

/**
 * camelCase'i snake_case'e dönüştürür
 * @param {string} str - camelCase string
 * @returns {string} snake_case string
 */
const toSnakeCase = (str) => {
    return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
};

/**
 * Nesne anahtarlarını dönüştürür (deep)
 * @param {Object} obj - Dönüştürülecek nesne
 * @param {Function} transformer - Anahtar dönüştürücü fonksiyon
 * @returns {Object} Dönüştürülmüş nesne
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
 * Backend response'unu frontend formatına dönüştürür
 */
export const fromBackend = (data) => transformKeys(data, toCamelCase);

/**
 * Frontend verisini backend formatına dönüştürür
 */
export const toBackend = (data) => transformKeys(data, toSnakeCase);

// ==================== Error Classes ====================

/**
 * API hata sınıfı
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
 * Network hata sınıfı
 */
export class NetworkError extends Error {
    constructor(message = 'Ağ bağlantısı hatası') {
        super(message);
        this.name = 'NetworkError';
    }
}

/**
 * Timeout hata sınıfı
 */
export class TimeoutError extends Error {
    constructor(message = 'İstek zaman aşımına uğradı') {
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
 * API isteği yapar ve sonucu işler
 * @param {string} endpoint - API endpoint (başında / ile)
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} API yanıtı (camelCase formatında)
 */
const request = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Default headers
    const headers = {
        ...options.headers
    };
    
    // JSON body için Content-Type ekle
    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(toBackend(options.body));
    }
    
    // JWT Token varsa ekle (localStorage'dan)
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
        
        // HTTP hata kontrolü
        if (!response.ok) {
            throw new ApiError(
                data.message || data.detail || 'Bir hata oluştu',
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
            throw new NetworkError('Backend sunucusuna bağlanılamadı. Sunucunun çalıştığından emin olun.');
        }
        
        // ApiError zaten doğru formatta
        if (error instanceof ApiError) {
            throw error;
        }
        
        // Diğer hatalar
        throw new ApiError(error.message, 0, 'CLIENT_ERROR');
    }
};

// ==================== API Methods ====================

/**
 * GET isteği
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
 * POST isteği (JSON body)
 */
export const post = (endpoint, body = {}) => {
    return request(endpoint, {
        method: 'POST',
        body
    });
};

/**
 * POST isteği (FormData - dosya yükleme için)
 */
export const postFormData = (endpoint, formData) => {
    return request(endpoint, {
        method: 'POST',
        body: formData
        // Content-Type otomatik ayarlanır (boundary ile)
    });
};

/**
 * PUT isteği
 */
export const put = (endpoint, body = {}) => {
    return request(endpoint, {
        method: 'PUT',
        body
    });
};

/**
 * DELETE isteği
 */
export const del = (endpoint) => {
    return request(endpoint, { method: 'DELETE' });
};

// ==================== Domain-Specific API Functions ====================

/**
 * Sistem sağlık kontrolü
 */
export const checkHealth = () => get('/api/health');

/**
 * Tıbbi görüntü analizi
 * @param {File} file - Yüklenecek dosya (DICOM, PNG, JPEG, etc.)
 * @returns {Promise<Object>} Analiz sonucu
 */
export const analyzeImage = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return postFormData('/api/analyze', formData);
};

/**
 * Hasta bilgisi getir
 * @param {string} patientId - Hasta ID
 */
export const getPatient = (patientId) => get(`/api/patients/${patientId}`);

/**
 * Tüm hastaları listele
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
