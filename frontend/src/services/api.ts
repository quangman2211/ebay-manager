import axios from 'axios';
import type { 
  User, Account, Order, Listing, LoginResponse, EnhancedAccount,
  UserAccountPermission, AccountSettings, BulkPermissionRequest, 
  BulkPermissionResponse, AccountSwitchRequest, AccountSwitchResponse,
  UserAccountPermissionCreate, AccountSettingsUpdate, AccountMetrics
} from '../types';
import { 
  getApiBaseUrl,
  API_ENDPOINTS,
  HTTP_HEADERS,
  REQUEST_CONFIG,
  FILE_UPLOAD
} from '../config/apiConstants';

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
});

// Add token to requests if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post(API_ENDPOINTS.AUTH.LOGIN, formData);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get(API_ENDPOINTS.AUTH.ME);
    return response.data;
  },
};

export const usersAPI = {
  getAllUsers: async (): Promise<User[]> => {
    const response = await api.get('/users');
    return response.data;
  },

  getUser: async (userId: number): Promise<User> => {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  },
};

export const accountsAPI = {
  getAccounts: async (includeInactive: boolean = false): Promise<Account[]> => {
    const response = await api.get(API_ENDPOINTS.ACCOUNTS.LIST, {
      params: includeInactive ? { include_inactive: true } : {}
    });
    return response.data;
  },

  createAccount: async (account: Omit<Account, 'id' | 'created_at'>): Promise<Account> => {
    const response = await api.post(API_ENDPOINTS.ACCOUNTS.CREATE, account);
    return response.data;
  },

  // Sprint 7: Enhanced account management
  getAccountDetails: async (accountId: number): Promise<EnhancedAccount> => {
    const response = await api.get(API_ENDPOINTS.ACCOUNTS.DETAILS(accountId));
    return response.data;
  },

  updateAccount: async (accountId: number, updates: Partial<Account>): Promise<Account> => {
    const response = await api.put(API_ENDPOINTS.ACCOUNTS.UPDATE(accountId), updates);
    return response.data;
  },

  deactivateAccount: async (accountId: number, action: string = 'transfer'): Promise<{
    action: string;
    message: string;
    account_id: number;
    account_name: string;
    data_impact?: any;
    transfer_summary?: any;
    deletion_summary?: any;
    next_action?: string;
  }> => {
    const response = await api.delete(API_ENDPOINTS.ACCOUNTS.DELETE(accountId), {
      params: { action }
    });
    return response.data;
  },

  getDeletionImpact: async (accountId: number): Promise<{
    account_id: number;
    account_name: string;
    is_active: boolean;
    can_delete: boolean;
    reason?: string;
    data_impact?: {
      orders: number;
      listings: number;
      permissions: number;
      settings: number;
      total_records: number;
    };
    is_guest_account: boolean;
  }> => {
    const response = await api.get(`/accounts/${accountId}/deletion-impact`);
    return response.data;
  },

  getGuestAccountSummary: async (): Promise<{
    guest_account_id: number;
    guest_account_name: string;
    total_orders: number;
    total_listings: number;
    total_records: number;
    original_accounts_count: number;
    original_accounts: string[];
  }> => {
    const response = await api.get('/guest-account/summary');
    return response.data;
  },

  switchAccount: async (request: AccountSwitchRequest): Promise<AccountSwitchResponse> => {
    const response = await api.post(API_ENDPOINTS.ACCOUNTS.SWITCH, request);
    return response.data;
  },
};

export const ordersAPI = {
  getOrders: async (accountId?: number, status?: string): Promise<Order[]> => {
    const params: Record<string, any> = {};
    if (accountId) params.account_id = accountId;
    if (status) params.status = status;
    
    const response = await api.get('/orders', { params });
    return response.data;
  },

  updateOrderStatus: async (orderId: number, status: string): Promise<void> => {
    await api.put(`/orders/${orderId}/status`, { status });
  },

  bulkUpdateOrderStatus: async (
    orderIds: number[], 
    status: string, 
    auditContext?: { userId: number; operation: string }
  ): Promise<import('../types').BulkOperationResult> => {
    const payload: any = { order_ids: orderIds, status };
    if (auditContext) {
      payload.audit_context = auditContext;
    }
    
    const response = await api.put('/orders/bulk/status', payload);
    return response.data;
  },
};

export const listingsAPI = {
  getListings: async (accountId?: number): Promise<Listing[]> => {
    const params: Record<string, any> = {};
    if (accountId) params.account_id = accountId;
    
    const response = await api.get('/listings', { params });
    return response.data;
  },
};

export const csvAPI = {
  uploadCSV: async (file: File, accountId: number, dataType: 'order' | 'listing'): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('account_id', accountId.toString());
    formData.append('data_type', dataType);
    
    const response = await api.post(API_ENDPOINTS.CSV.UPLOAD, formData, {
      headers: {
        'Content-Type': HTTP_HEADERS.CONTENT_TYPE.FORM_DATA,
      },
      timeout: REQUEST_CONFIG.CSV_UPLOAD_TIMEOUT,
    });
    return response.data;
  },

  uploadCSVEnhanced: async (file: File, accountId: number, dataType: 'order' | 'listing'): Promise<{
    success: boolean;
    upload_id?: string;
    message: string;
    inserted_count?: number;
    duplicate_count?: number;
    total_records?: number;
    detected_username?: string;
    error?: {
      code: string;
      message: string;
      suggestions: string[];
    };
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('account_id', accountId.toString());
    formData.append('data_type', dataType);
    
    const response = await api.post(API_ENDPOINTS.CSV.UPLOAD_ENHANCED, formData, {
      headers: {
        'Content-Type': HTTP_HEADERS.CONTENT_TYPE.FORM_DATA,
      },
      timeout: REQUEST_CONFIG.CSV_UPLOAD_TIMEOUT,
    });
    return response.data;
  },

  suggestAccountsForCSV: async (file: File): Promise<{
    detected_username: string | null;
    suggested_accounts: Array<{
      id: number;
      name: string;
      platform_username: string | null;
      match_type: 'exact' | 'partial';
    }>;
    total_suggestions: number;
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(API_ENDPOINTS.ACCOUNTS.SUGGEST, formData, {
      headers: {
        'Content-Type': HTTP_HEADERS.CONTENT_TYPE.FORM_DATA,
      },
      timeout: REQUEST_CONFIG.CSV_UPLOAD_TIMEOUT,
    });
    return response.data;
  },

  getUploadProgress: async (uploadId: string): Promise<{
    success: boolean;
    upload_id?: string;
    filename?: string;
    state?: 'processing' | 'completed' | 'failed';
    message?: string;
    progress_percent?: number;
    started_at?: string;
    error?: string;
  }> => {
    const response = await api.get(API_ENDPOINTS.UPLOAD.PROGRESS(uploadId), {
      timeout: REQUEST_CONFIG.DEFAULT_TIMEOUT,
    });
    return response.data;
  },
};

export const searchAPI = {
  globalSearch: async (query: string): Promise<any[]> => {
    const response = await api.get('/search', {
      params: { q: query }
    });
    return response.data;
  },
};

// Sprint 7: Permission Management APIs
export const permissionsAPI = {
  createUserPermission: async (accountId: number, permission: UserAccountPermissionCreate): Promise<UserAccountPermission> => {
    const response = await api.post(`/accounts/${accountId}/permissions`, permission);
    return response.data;
  },

  getAccountPermissions: async (accountId: number): Promise<UserAccountPermission[]> => {
    const response = await api.get(`/accounts/${accountId}/permissions`);
    return response.data;
  },

  getUserPermissions: async (userId: number): Promise<UserAccountPermission[]> => {
    const response = await api.get(`/users/${userId}/permissions`);
    return response.data;
  },

  updateUserPermission: async (accountId: number, permissionId: number, updates: Partial<UserAccountPermissionCreate>): Promise<UserAccountPermission> => {
    const response = await api.put(`/accounts/${accountId}/permissions/${permissionId}`, updates);
    return response.data;
  },

  deleteUserPermission: async (accountId: number, permissionId: number): Promise<void> => {
    await api.delete(`/accounts/${accountId}/permissions/${permissionId}`);
  },

  bulkUpdatePermissions: async (request: BulkPermissionRequest): Promise<BulkPermissionResponse> => {
    const response = await api.post(`/accounts/${request.account_id}/permissions/bulk`, request);
    return response.data;
  },
};

// Sprint 7: Settings Management APIs
export const settingsAPI = {
  getAccountSettings: async (accountId: number): Promise<AccountSettings[]> => {
    const response = await api.get(`/accounts/${accountId}/settings`);
    return response.data;
  },

  updateAccountSettings: async (accountId: number, settings: AccountSettingsUpdate[]): Promise<{ message: string; updated_count: number }> => {
    const response = await api.put(`/accounts/${accountId}/settings`, settings);
    return response.data;
  },
};

// Sprint 7: Metrics Management APIs
export const metricsAPI = {
  getAccountMetrics: async (accountId: number, period: '7d' | '30d' | '90d' | '1y' = '30d'): Promise<AccountMetrics[]> => {
    const response = await api.get(`/accounts/${accountId}/metrics`, {
      params: { period }
    });
    return response.data;
  },

  getMetricsSummary: async (accountId: number): Promise<{
    total_revenue: number;
    total_orders: number;
    active_listings: number;
    conversion_rate: number;
  }> => {
    const response = await api.get(`/accounts/${accountId}/metrics/summary`);
    return response.data;
  },
};

export default api;