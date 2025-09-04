/**
 * API configuration constants
 * Centralized to eliminate hardcoded values (SOLID compliance)
 * 
 * Following SOLID principles:
 * - Single Responsibility: Only API-related constants
 * - Open/Closed: Extensible for new API endpoints
 * - Dependency Inversion: API layer depends on abstractions via constants
 */

// Base Configuration
export const API_CONFIG = {
  DEFAULT_BASE_URL: 'http://localhost:8000',
  API_VERSION: 'v1',
  TIMEOUT_MS: 10000,
  RETRY_COUNT: 3,
  RETRY_DELAY_MS: 1000,
} as const;

// API Endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/login',
    ME: '/me',
  },
  ACCOUNTS: {
    LIST: '/accounts',
    CREATE: '/accounts',
    DETAILS: (id: number) => `/accounts/${id}/details`,
    UPDATE: (id: number) => `/accounts/${id}`,
    DELETE: (id: number) => `/accounts/${id}`,
    SWITCH: '/accounts/switch',
    SUGGEST: '/accounts/suggest',
    PERMISSIONS: (id: number) => `/accounts/${id}/permissions`,
    SETTINGS: (id: number) => `/accounts/${id}/settings`,
    BULK_PERMISSIONS: (id: number) => `/accounts/${id}/permissions/bulk`,
  },
  CSV: {
    UPLOAD: '/csv/upload',
  },
  ORDERS: {
    LIST: '/orders',
    UPDATE_STATUS: (id: number) => `/orders/${id}/status`,
    BULK_STATUS: '/orders/bulk/status',
  },
  LISTINGS: {
    LIST: '/listings',
  },
  SEARCH: {
    GLOBAL: '/search',
  },
  USERS: {
    LIST: '/users',
    DETAILS: (id: number) => `/users/${id}`,
    PERMISSIONS: (id: number) => `/users/${id}/permissions`,
  },
  PERMISSIONS: {
    UPDATE: (id: number) => `/permissions/${id}`,
    DELETE: (id: number) => `/permissions/${id}`,
  },
} as const;

// HTTP Headers
export const HTTP_HEADERS = {
  CONTENT_TYPE: {
    JSON: 'application/json',
    FORM_DATA: 'multipart/form-data',
    URL_ENCODED: 'application/x-www-form-urlencoded',
  },
  AUTHORIZATION: 'Authorization',
  BEARER_PREFIX: 'Bearer ',
} as const;

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  INTERNAL_SERVER_ERROR: 500,
} as const;

// Request/Response Configuration
export const REQUEST_CONFIG = {
  DEFAULT_TIMEOUT: 120000, // 2 minutes for CSV uploads
  CSV_UPLOAD_TIMEOUT: 600000, // 10 minutes for large CSV files
  BULK_OPERATION_TIMEOUT: 300000, // 5 minutes for bulk operations
} as const;

// File Upload Configuration  
export const FILE_UPLOAD = {
  ACCEPTED_TYPES: {
    CSV: ['text/csv', 'application/vnd.ms-excel'],
  },
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  CHUNK_SIZE: 1024 * 1024, // 1MB chunks
} as const;

// Environment Configuration
export const getApiBaseUrl = (): string => {
  return process.env.REACT_APP_API_URL || API_CONFIG.DEFAULT_BASE_URL;
};

export const getFullApiUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  return `${baseUrl}/api/${API_CONFIG.API_VERSION}${endpoint}`;
};

// Error Messages
export const API_ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection failed. Please check your internet connection.',
  UNAUTHORIZED: 'Session expired. Please log in again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error occurred. Please try again later.',
  TIMEOUT: 'Request timed out. Please try again.',
  UNKNOWN: 'An unexpected error occurred. Please try again.',
} as const;