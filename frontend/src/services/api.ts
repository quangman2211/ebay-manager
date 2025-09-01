import axios from 'axios';
import type { User, Account, Order, Listing, LoginResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
    
    const response = await api.post('/login', formData);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/me');
    return response.data;
  },
};

export const accountsAPI = {
  getAccounts: async (): Promise<Account[]> => {
    const response = await api.get('/accounts');
    return response.data;
  },

  createAccount: async (account: Omit<Account, 'id' | 'created_at'>): Promise<Account> => {
    const response = await api.post('/accounts', account);
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
    
    const response = await api.post('/csv/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
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

export default api;