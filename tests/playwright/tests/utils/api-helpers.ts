import { APIRequestContext, expect } from '@playwright/test';
import axios from 'axios';
import { testCredentials, apiEndpoints } from '../fixtures/test-data';

/**
 * API helper functions for backend testing
 */

export class ApiHelper {
  constructor(private request: APIRequestContext) {}

  /**
   * Login and get access token
   */
  async login(username: string = testCredentials.admin.username, password: string = testCredentials.admin.password): Promise<string> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await this.request.post(`${apiEndpoints.backend}${apiEndpoints.login}`, {
      data: formData.toString(),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    return data.access_token;
  }

  /**
   * Get authorization headers with token
   */
  getAuthHeaders(token: string) {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  /**
   * Create a test eBay account
   */
  async createAccount(token: string, accountData = {
    name: 'Test Account',
    ebay_username: 'test_user',
    is_active: true
  }): Promise<any> {
    const response = await this.request.post(`${apiEndpoints.backend}${apiEndpoints.accounts}`, {
      data: accountData,
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Get all accounts
   */
  async getAccounts(token: string): Promise<any[]> {
    const response = await this.request.get(`${apiEndpoints.backend}${apiEndpoints.accounts}`, {
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Upload CSV file
   */
  async uploadCSV(token: string, filePath: string, accountId: number, dataType: 'order' | 'listing'): Promise<any> {
    const response = await this.request.post(`${apiEndpoints.backend}${apiEndpoints.csvUpload}`, {
      multipart: {
        file: filePath,
        account_id: accountId.toString(),
        data_type: dataType,
      },
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Get orders for an account
   */
  async getOrders(token: string, accountId: number, status?: string): Promise<any[]> {
    let url = `${apiEndpoints.backend}${apiEndpoints.orders}?account_id=${accountId}`;
    if (status) {
      url += `&status=${status}`;
    }

    const response = await this.request.get(url, {
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Update order status
   */
  async updateOrderStatus(token: string, orderId: number, status: string): Promise<any> {
    const response = await this.request.put(`${apiEndpoints.backend}${apiEndpoints.orders}/${orderId}/status`, {
      data: { status },
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Get listings for an account
   */
  async getListings(token: string, accountId: number): Promise<any[]> {
    const response = await this.request.get(`${apiEndpoints.backend}${apiEndpoints.listings}?account_id=${accountId}`, {
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Update order tracking number
   */
  async updateOrderTracking(token: string, orderId: number, trackingNumber: string): Promise<any> {
    const response = await this.request.put(`${apiEndpoints.backend}${apiEndpoints.orderTracking.replace('{id}', orderId.toString())}`, {
      data: { tracking_number: trackingNumber },
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Add note to order
   */
  async addOrderNote(token: string, orderId: number, note: string): Promise<any> {
    const response = await this.request.post(`${apiEndpoints.backend}${apiEndpoints.orderNotes.replace('{id}', orderId.toString())}`, {
      data: { note },
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Get order notes
   */
  async getOrderNotes(token: string, orderId: number): Promise<any[]> {
    const response = await this.request.get(`${apiEndpoints.backend}${apiEndpoints.orderNotes.replace('{id}', orderId.toString())}`, {
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Get order history
   */
  async getOrderHistory(token: string, orderId: number): Promise<any[]> {
    const response = await this.request.get(`${apiEndpoints.backend}${apiEndpoints.orderHistory.replace('{id}', orderId.toString())}`, {
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }

  /**
   * Get single order details
   */
  async getOrder(token: string, orderId: number): Promise<any> {
    const response = await this.request.get(`${apiEndpoints.backend}${apiEndpoints.orders}/${orderId}`, {
      headers: this.getAuthHeaders(token),
    });

    expect(response.ok()).toBeTruthy();
    return await response.json();
  }
}

/**
 * Screenshot helper for API documentation
 */
export async function captureAPIDocumentation(request: APIRequestContext, outputPath: string): Promise<void> {
  const response = await request.get(`${apiEndpoints.backend}${apiEndpoints.docs}`);
  expect(response.ok()).toBeTruthy();
  
  // Get HTML content
  const html = await response.text();
  
  // Use axios to get a more detailed response for screenshot purposes
  try {
    const axiosResponse = await axios.get(`${apiEndpoints.backend}${apiEndpoints.docs}`);
    console.log(`API Documentation available at: ${apiEndpoints.backend}${apiEndpoints.docs}`);
  } catch (error) {
    console.error('Failed to capture API docs:', error);
  }
}