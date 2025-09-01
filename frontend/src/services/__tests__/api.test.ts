// Mock axios before any imports that use it
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    defaults: { headers: {} },
  })),
}));

import axios from 'axios';
import { authAPI, accountsAPI, ordersAPI, listingsAPI, csvAPI, searchAPI } from '../api';
import type { User, Account, Order, Listing, LoginResponse } from '../../types';

const mockedAxios = axios as jest.Mocked<typeof axios>;

// Get the mock axios instance
const mockAxiosInstance = mockedAxios.create() as any;

describe('API Services', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('authAPI', () => {
    describe('login', () => {
      it('should login successfully with correct credentials', async () => {
        const mockResponse: LoginResponse = {
          access_token: 'test-token',
          token_type: 'bearer',
          user: {
            id: 1,
            username: 'testuser',
            email: 'test@example.com',
            role: 'admin',
            is_active: true,
          },
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResponse });

        const result = await authAPI.login('testuser', 'password');

        expect(mockAxiosInstance.post).toHaveBeenCalledWith('/login', expect.any(FormData));
        expect(result).toEqual(mockResponse);
      });

      it('should handle login failure', async () => {
        const errorResponse = {
          response: {
            status: 401,
            data: { detail: 'Invalid credentials' },
          },
        };

        mockAxiosInstance.post.mockRejectedValueOnce(errorResponse);

        await expect(authAPI.login('invaliduser', 'wrongpass')).rejects.toEqual(errorResponse);
      });

      it('should properly format FormData for login request', async () => {
        mockAxiosInstance.post.mockResolvedValueOnce({ data: {} });

        await authAPI.login('username', 'password');

        const formData = mockAxiosInstance.post.mock.calls[0][1];
        expect(formData).toBeInstanceOf(FormData);
      });
    });

    describe('getCurrentUser', () => {
      it('should get current user successfully', async () => {
        const mockUser: User = {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'admin',
          is_active: true,
        };

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockUser });

        const result = await authAPI.getCurrentUser();

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/me');
        expect(result).toEqual(mockUser);
      });

      it('should handle unauthorized user request', async () => {
        const errorResponse = {
          response: { status: 401 },
        };

        mockAxiosInstance.get.mockRejectedValueOnce(errorResponse);

        await expect(authAPI.getCurrentUser()).rejects.toEqual(errorResponse);
      });
    });
  });

  describe('accountsAPI', () => {
    describe('getAccounts', () => {
      it('should fetch accounts successfully', async () => {
        const mockAccounts: Account[] = [
          {
            id: 1,
            name: 'Test Account 1',
            username: 'testuser1',
            created_at: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            name: 'Test Account 2',
            username: 'testuser2',
            created_at: '2024-01-01T00:00:00Z',
          },
        ];

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockAccounts });

        const result = await accountsAPI.getAccounts();

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/accounts');
        expect(result).toEqual(mockAccounts);
      });

      it('should handle empty accounts list', async () => {
        mockAxiosInstance.get.mockResolvedValueOnce({ data: [] });

        const result = await accountsAPI.getAccounts();

        expect(result).toEqual([]);
      });
    });

    describe('createAccount', () => {
      it('should create account successfully', async () => {
        const newAccount = {
          name: 'New Account',
          username: 'newuser',
        };

        const createdAccount: Account = {
          id: 3,
          ...newAccount,
          created_at: '2024-01-01T00:00:00Z',
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: createdAccount });

        const result = await accountsAPI.createAccount(newAccount);

        expect(mockAxiosInstance.post).toHaveBeenCalledWith('/accounts', newAccount);
        expect(result).toEqual(createdAccount);
      });

      it('should handle account creation validation errors', async () => {
        const newAccount = { name: '', username: '' };
        const errorResponse = {
          response: {
            status: 422,
            data: { detail: 'Validation error' },
          },
        };

        mockAxiosInstance.post.mockRejectedValueOnce(errorResponse);

        await expect(accountsAPI.createAccount(newAccount)).rejects.toEqual(errorResponse);
      });
    });
  });

  describe('ordersAPI', () => {
    describe('getOrders', () => {
      it('should fetch orders without filters', async () => {
        const mockOrders: Order[] = [
          {
            id: 1,
            item_id: 'ORD-001',
            order_status: { status: 'pending' },
            csv_row: {
              'Order Number': 'ORD-001',
              'Buyer Username': 'buyer1',
              'Sale Amount': '$29.99',
            },
          },
        ];

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockOrders });

        const result = await ordersAPI.getOrders();

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/orders', { params: {} });
        expect(result).toEqual(mockOrders);
      });

      it('should fetch orders with account filter', async () => {
        const mockOrders: Order[] = [];
        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockOrders });

        const result = await ordersAPI.getOrders(1);

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/orders', {
          params: { account_id: 1 },
        });
        expect(result).toEqual(mockOrders);
      });

      it('should fetch orders with status filter', async () => {
        const mockOrders: Order[] = [];
        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockOrders });

        const result = await ordersAPI.getOrders(undefined, 'pending');

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/orders', {
          params: { status: 'pending' },
        });
        expect(result).toEqual(mockOrders);
      });

      it('should fetch orders with both account and status filters', async () => {
        const mockOrders: Order[] = [];
        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockOrders });

        const result = await ordersAPI.getOrders(1, 'shipped');

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/orders', {
          params: { account_id: 1, status: 'shipped' },
        });
      });
    });

    describe('updateOrderStatus', () => {
      it('should update single order status', async () => {
        mockAxiosInstance.put.mockResolvedValueOnce({ data: {} });

        await ordersAPI.updateOrderStatus(1, 'shipped');

        expect(mockAxiosInstance.put).toHaveBeenCalledWith('/orders/1/status', {
          status: 'shipped',
        });
      });

      it('should handle order not found error', async () => {
        const errorResponse = {
          response: {
            status: 404,
            data: { detail: 'Order not found' },
          },
        };

        mockAxiosInstance.put.mockRejectedValueOnce(errorResponse);

        await expect(ordersAPI.updateOrderStatus(999, 'shipped')).rejects.toEqual(errorResponse);
      });
    });

    describe('bulkUpdateOrderStatus', () => {
      it('should perform bulk update without audit context', async () => {
        const mockResult = {
          successful: [1, 2, 3],
          failed: [],
          totalProcessed: 3,
          errors: [],
        };

        mockAxiosInstance.put.mockResolvedValueOnce({ data: mockResult });

        const result = await ordersAPI.bulkUpdateOrderStatus([1, 2, 3], 'processing');

        expect(mockAxiosInstance.put).toHaveBeenCalledWith('/orders/bulk/status', {
          order_ids: [1, 2, 3],
          status: 'processing',
        });
        expect(result).toEqual(mockResult);
      });

      it('should perform bulk update with audit context', async () => {
        const mockResult = {
          successful: [1],
          failed: [2],
          totalProcessed: 2,
          errors: ['Order 2: Invalid status transition'],
        };

        const auditContext = { userId: 1, operation: 'bulk_status_update' };

        mockAxiosInstance.put.mockResolvedValueOnce({ data: mockResult });

        const result = await ordersAPI.bulkUpdateOrderStatus([1, 2], 'completed', auditContext);

        expect(mockAxiosInstance.put).toHaveBeenCalledWith('/orders/bulk/status', {
          order_ids: [1, 2],
          status: 'completed',
          audit_context: auditContext,
        });
        expect(result).toEqual(mockResult);
      });

      it('should handle bulk update partial failures', async () => {
        const mockResult = {
          successful: [1, 2],
          failed: [3],
          totalProcessed: 3,
          errors: ['Order 3: Already shipped'],
        };

        mockAxiosInstance.put.mockResolvedValueOnce({ data: mockResult });

        const result = await ordersAPI.bulkUpdateOrderStatus([1, 2, 3], 'completed');

        expect(result.successful).toEqual([1, 2]);
        expect(result.failed).toEqual([3]);
        expect(result.errors).toContain('Order 3: Already shipped');
      });
    });
  });

  describe('listingsAPI', () => {
    describe('getListings', () => {
      it('should fetch listings without account filter', async () => {
        const mockListings: Listing[] = [
          {
            id: 1,
            item_id: 'ITEM-001',
            listing_status: { status: 'active' },
            csv_row: {
              'Item Number': 'ITEM-001',
              'Item Title': 'Test Item',
              'Current Price': '$19.99',
            },
          },
        ];

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockListings });

        const result = await listingsAPI.getListings();

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/listings', { params: {} });
        expect(result).toEqual(mockListings);
      });

      it('should fetch listings with account filter', async () => {
        const mockListings: Listing[] = [];
        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockListings });

        const result = await listingsAPI.getListings(2);

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/listings', {
          params: { account_id: 2 },
        });
        expect(result).toEqual(mockListings);
      });
    });
  });

  describe('csvAPI', () => {
    describe('uploadCSV', () => {
      it('should upload order CSV successfully', async () => {
        const mockFile = new File(['test,data'], 'orders.csv', { type: 'text/csv' });
        const mockResponse = {
          success: true,
          recordsProcessed: 10,
          errors: [],
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResponse });

        const result = await csvAPI.uploadCSV(mockFile, 1, 'order');

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          '/csv/upload',
          expect.any(FormData),
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );
        expect(result).toEqual(mockResponse);
      });

      it('should upload listing CSV successfully', async () => {
        const mockFile = new File(['test,data'], 'listings.csv', { type: 'text/csv' });
        const mockResponse = {
          success: true,
          recordsProcessed: 5,
          errors: [],
        };

        mockAxiosInstance.post.mockResolvedValueOnce({ data: mockResponse });

        const result = await csvAPI.uploadCSV(mockFile, 2, 'listing');

        const formData = mockAxiosInstance.post.mock.calls[0][1];
        expect(formData).toBeInstanceOf(FormData);
      });

      it('should handle CSV upload validation errors', async () => {
        const mockFile = new File(['invalid,data'], 'invalid.csv', { type: 'text/csv' });
        const errorResponse = {
          response: {
            status: 400,
            data: { detail: 'Invalid CSV format' },
          },
        };

        mockAxiosInstance.post.mockRejectedValueOnce(errorResponse);

        await expect(csvAPI.uploadCSV(mockFile, 1, 'order')).rejects.toEqual(errorResponse);
      });

      it('should properly format FormData for CSV upload', async () => {
        const mockFile = new File(['test'], 'test.csv');
        mockAxiosInstance.post.mockResolvedValueOnce({ data: {} });

        await csvAPI.uploadCSV(mockFile, 3, 'listing');

        const formData = mockAxiosInstance.post.mock.calls[0][1];
        expect(formData).toBeInstanceOf(FormData);
      });
    });
  });

  describe('searchAPI', () => {
    describe('globalSearch', () => {
      it('should perform global search successfully', async () => {
        const mockResults = [
          { type: 'order', id: 1, title: 'Order ORD-001' },
          { type: 'listing', id: 2, title: 'Item ITEM-002' },
        ];

        mockAxiosInstance.get.mockResolvedValueOnce({ data: mockResults });

        const result = await searchAPI.globalSearch('test query');

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/search', {
          params: { q: 'test query' },
        });
        expect(result).toEqual(mockResults);
      });

      it('should handle empty search results', async () => {
        mockAxiosInstance.get.mockResolvedValueOnce({ data: [] });

        const result = await searchAPI.globalSearch('nonexistent');

        expect(result).toEqual([]);
      });

      it('should handle search with special characters', async () => {
        mockAxiosInstance.get.mockResolvedValueOnce({ data: [] });

        await searchAPI.globalSearch('test@example.com');

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/search', {
          params: { q: 'test@example.com' },
        });
      });
    });
  });

  describe('Axios Configuration', () => {
    it('should create axios instance with correct base URL', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8000/api/v1',
      });
    });

    it('should set up request interceptor', () => {
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
    });

    it('should set up response interceptor', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('Token Management', () => {
    beforeEach(() => {
      // Mock localStorage
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: jest.fn(),
          setItem: jest.fn(),
          removeItem: jest.fn(),
          clear: jest.fn(),
        },
        writable: true,
      });

      // Mock window.location
      delete (window as any).location;
      window.location = { href: '' } as any;
    });

    it('should add token to request headers when token exists', () => {
      const mockGetItem = jest.spyOn(Storage.prototype, 'getItem');
      mockGetItem.mockReturnValue('test-token');

      // Simulate the request interceptor
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      const config = { headers: {} };

      const result = requestInterceptor(config);

      expect(result.headers.Authorization).toBe('Bearer test-token');
    });

    it('should not add token to request headers when no token exists', () => {
      const mockGetItem = jest.spyOn(Storage.prototype, 'getItem');
      mockGetItem.mockReturnValue(null);

      // Simulate the request interceptor
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      const config = { headers: {} };

      const result = requestInterceptor(config);

      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should handle 401 errors by clearing token and redirecting', () => {
      const mockRemoveItem = jest.spyOn(Storage.prototype, 'removeItem');
      
      // Simulate the response interceptor error handler
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      const error = {
        response: { status: 401 },
      };

      expect(() => responseInterceptor(error)).toThrow();
      expect(mockRemoveItem).toHaveBeenCalledWith('token');
      expect(window.location.href).toBe('/login');
    });

    it('should pass through non-401 errors', () => {
      // Simulate the response interceptor error handler
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      const error = {
        response: { status: 500 },
      };

      expect(() => responseInterceptor(error)).toThrow();
    });

    it('should pass through successful responses', () => {
      // Simulate the response interceptor success handler
      const responseInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][0];
      const response = { data: 'test' };

      const result = responseInterceptor(response);

      expect(result).toEqual(response);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      mockAxiosInstance.get.mockRejectedValueOnce(networkError);

      await expect(authAPI.getCurrentUser()).rejects.toThrow('Network Error');
    });

    it('should handle timeout errors', async () => {
      const timeoutError = { code: 'ECONNABORTED' };
      mockAxiosInstance.post.mockRejectedValueOnce(timeoutError);

      await expect(authAPI.login('user', 'pass')).rejects.toEqual(timeoutError);
    });

    it('should handle malformed response errors', async () => {
      const malformedError = { response: { status: 200, data: 'invalid json' } };
      mockAxiosInstance.get.mockRejectedValueOnce(malformedError);

      await expect(accountsAPI.getAccounts()).rejects.toEqual(malformedError);
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined parameters gracefully', async () => {
      mockAxiosInstance.get.mockResolvedValueOnce({ data: [] });

      await ordersAPI.getOrders(undefined, undefined);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/orders', { params: {} });
    });

    it('should handle empty arrays in bulk operations', async () => {
      const mockResult = {
        successful: [],
        failed: [],
        totalProcessed: 0,
        errors: [],
      };

      mockAxiosInstance.put.mockResolvedValueOnce({ data: mockResult });

      const result = await ordersAPI.bulkUpdateOrderStatus([], 'processing');

      expect(result.totalProcessed).toBe(0);
    });

    it('should handle very large bulk operations', async () => {
      const largeOrderIds = Array.from({ length: 1000 }, (_, i) => i + 1);
      const mockResult = {
        successful: largeOrderIds,
        failed: [],
        totalProcessed: 1000,
        errors: [],
      };

      mockAxiosInstance.put.mockResolvedValueOnce({ data: mockResult });

      const result = await ordersAPI.bulkUpdateOrderStatus(largeOrderIds, 'processing');

      expect(result.successful).toHaveLength(1000);
    });
  });
});