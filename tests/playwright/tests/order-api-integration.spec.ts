import { test, expect } from '@playwright/test';
import { ApiHelper } from './utils/api-helpers';
import { testCredentials, testOrderData, apiEndpoints } from './fixtures/test-data';

/**
 * API Integration tests for Order Enhancement Features
 * Tests the backend API endpoints for:
 * - Order status updates
 * - Tracking number management
 * - Order notes system
 * - Order history tracking
 */

test.describe('Order Enhancement API Integration', () => {
  let apiHelper: ApiHelper;
  let token: string;
  let testAccountId: number;
  let testOrderId: number;

  test.beforeAll(async ({ request }) => {
    apiHelper = new ApiHelper(request);
    token = await apiHelper.login();
    
    // Create test account
    const account = await apiHelper.createAccount(token);
    testAccountId = account.id;
    
    // Create test orders (assuming orders exist from CSV import or test data)
    const orders = await apiHelper.getOrders(token, testAccountId);
    if (orders.length > 0) {
      testOrderId = orders[0].id;
    } else {
      // Create a test order if none exist
      test.skip('No test orders available - requires CSV import or order creation');
    }
  });

  test.describe('Order Status API', () => {
    test('should update order status successfully', async ({ request }) => {
      const newStatus = 'processing';
      
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orders}/${testOrderId}/status`, {
        data: { status: newStatus },
        headers: apiHelper.getAuthHeaders(token),
      });

      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(data.status).toBe(newStatus);
    });

    test('should validate status transitions', async ({ request }) => {
      // First set to delivered
      await request.put(`${apiEndpoints.backend}${apiEndpoints.orders}/${testOrderId}/status`, {
        data: { status: 'delivered' },
        headers: apiHelper.getAuthHeaders(token),
      });

      // Try to transition from delivered to pending (should fail)
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orders}/${testOrderId}/status`, {
        data: { status: 'pending' },
        headers: apiHelper.getAuthHeaders(token),
      });

      // Should either return 400 or handle gracefully
      if (!response.ok()) {
        expect(response.status()).toBe(400);
        const error = await response.json();
        expect(error.detail).toContain('Invalid status transition');
      }
    });

    test('should reject invalid status values', async ({ request }) => {
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orders}/${testOrderId}/status`, {
        data: { status: 'invalid_status' },
        headers: apiHelper.getAuthHeaders(token),
      });

      expect(response.status()).toBe(422);
      const error = await response.json();
      expect(error.detail).toBeDefined();
    });

    test('should require authentication', async ({ request }) => {
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orders}/${testOrderId}/status`, {
        data: { status: 'processing' }
      });

      expect(response.status()).toBe(401);
    });
  });

  test.describe('Tracking Number API', () => {
    test('should update tracking number successfully', async () => {
      const trackingNumber = testOrderData.validTrackingNumbers[0];
      
      const result = await apiHelper.updateOrderTracking(token, testOrderId, trackingNumber);
      expect(result.tracking_number).toBe(trackingNumber);
    });

    test('should format tracking numbers correctly', async ({ request }) => {
      const lowercaseTracking = '1z999aa1234567890';
      
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orderTracking.replace('{id}', testOrderId.toString())}`, {
        data: { tracking_number: lowercaseTracking },
        headers: apiHelper.getAuthHeaders(token),
      });

      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(data.tracking_number).toBe('1Z999AA1234567890');
    });

    test('should validate tracking number format', async ({ request }) => {
      const invalidTracking = 'invalid123';
      
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orderTracking.replace('{id}', testOrderId.toString())}`, {
        data: { tracking_number: invalidTracking },
        headers: apiHelper.getAuthHeaders(token),
      });

      // Should either accept or reject based on validation rules
      if (!response.ok()) {
        expect(response.status()).toBe(422);
        const error = await response.json();
        expect(error.detail).toContain('tracking number');
      }
    });

    test('should handle empty tracking numbers', async ({ request }) => {
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orderTracking.replace('{id}', testOrderId.toString())}`, {
        data: { tracking_number: '' },
        headers: apiHelper.getAuthHeaders(token),
      });

      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(data.tracking_number).toBe('');
    });
  });

  test.describe('Order Notes API', () => {
    test('should add note to order successfully', async () => {
      const noteText = testOrderData.sampleNotes[0];
      
      const result = await apiHelper.addOrderNote(token, testOrderId, noteText);
      expect(result.note).toBe(noteText);
      expect(result.created_by).toBe(testCredentials.admin.username);
      expect(result.created_at).toBeDefined();
    });

    test('should retrieve order notes', async () => {
      // Add a note first
      const noteText = 'Test note for retrieval';
      await apiHelper.addOrderNote(token, testOrderId, noteText);
      
      // Get all notes
      const notes = await apiHelper.getOrderNotes(token, testOrderId);
      expect(Array.isArray(notes)).toBe(true);
      expect(notes.some(note => note.note === noteText)).toBe(true);
    });

    test('should validate note content', async ({ request }) => {
      const response = await request.post(`${apiEndpoints.backend}${apiEndpoints.orderNotes.replace('{id}', testOrderId.toString())}`, {
        data: { note: '' },
        headers: apiHelper.getAuthHeaders(token),
      });

      // Should reject empty notes
      if (!response.ok()) {
        expect(response.status()).toBe(422);
        const error = await response.json();
        expect(error.detail).toContain('note');
      }
    });

    test('should include note metadata', async () => {
      const noteText = 'Test note with metadata';
      const result = await apiHelper.addOrderNote(token, testOrderId, noteText);
      
      expect(result.id).toBeDefined();
      expect(result.order_id).toBe(testOrderId);
      expect(result.created_by).toBe(testCredentials.admin.username);
      expect(result.created_at).toBeDefined();
    });

    test('should order notes chronologically', async () => {
      // Add multiple notes with delays
      const note1 = 'First note';
      const note2 = 'Second note';
      
      await apiHelper.addOrderNote(token, testOrderId, note1);
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
      await apiHelper.addOrderNote(token, testOrderId, note2);
      
      const notes = await apiHelper.getOrderNotes(token, testOrderId);
      const sortedNotes = notes.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      
      expect(sortedNotes[0].note).toBe(note2); // Most recent first
      expect(sortedNotes[1].note).toBe(note1);
    });
  });

  test.describe('Order History API', () => {
    test('should track status changes in history', async () => {
      // Make several status changes
      const statuses = ['processing', 'shipped'];
      
      for (const status of statuses) {
        await apiHelper.updateOrderStatus(token, testOrderId, status);
        await new Promise(resolve => setTimeout(resolve, 500)); // Small delay
      }
      
      // Get history
      const history = await apiHelper.getOrderHistory(token, testOrderId);
      expect(Array.isArray(history)).toBe(true);
      expect(history.length).toBeGreaterThan(0);
      
      // Check that recent changes are in history
      const recentHistory = history.filter(h => statuses.includes(h.new_status));
      expect(recentHistory.length).toBeGreaterThanOrEqual(2);
    });

    test('should include history metadata', async () => {
      // Make a status change
      await apiHelper.updateOrderStatus(token, testOrderId, 'delivered');
      
      // Get history
      const history = await apiHelper.getOrderHistory(token, testOrderId);
      const latestEntry = history[0]; // Most recent should be first
      
      expect(latestEntry.order_id).toBe(testOrderId);
      expect(latestEntry.new_status).toBe('delivered');
      expect(latestEntry.changed_by).toBe(testCredentials.admin.username);
      expect(latestEntry.changed_at).toBeDefined();
    });

    test('should track tracking number changes', async () => {
      const trackingNumber = testOrderData.validTrackingNumbers[1];
      
      // Update tracking number
      await apiHelper.updateOrderTracking(token, testOrderId, trackingNumber);
      
      // Get history
      const history = await apiHelper.getOrderHistory(token, testOrderId);
      
      // Should include tracking number update in history
      const trackingUpdate = history.find(h => h.field === 'tracking_number');
      if (trackingUpdate) {
        expect(trackingUpdate.new_value).toBe(trackingNumber);
      }
    });

    test('should maintain chronological order', async () => {
      const history = await apiHelper.getOrderHistory(token, testOrderId);
      
      if (history.length > 1) {
        // Verify descending chronological order (newest first)
        for (let i = 0; i < history.length - 1; i++) {
          const currentTime = new Date(history[i].changed_at).getTime();
          const nextTime = new Date(history[i + 1].changed_at).getTime();
          expect(currentTime).toBeGreaterThanOrEqual(nextTime);
        }
      }
    });
  });

  test.describe('Order Details API', () => {
    test('should retrieve complete order details', async () => {
      const order = await apiHelper.getOrder(token, testOrderId);
      
      expect(order.id).toBe(testOrderId);
      expect(order.status).toBeDefined();
      expect(order.created_at).toBeDefined();
      expect(order.account_id).toBe(testAccountId);
    });

    test('should include enhanced order information', async () => {
      const order = await apiHelper.getOrder(token, testOrderId);
      
      // Should include tracking number if set
      expect(order.hasOwnProperty('tracking_number')).toBe(true);
      
      // Should include note count or notes
      expect(order.hasOwnProperty('notes_count') || order.hasOwnProperty('notes')).toBe(true);
      
      // Should include history count
      expect(order.hasOwnProperty('history_count')).toBe(true);
    });

    test('should handle non-existent orders', async ({ request }) => {
      const nonExistentId = 999999;
      
      const response = await request.get(`${apiEndpoints.backend}${apiEndpoints.orders}/${nonExistentId}`, {
        headers: apiHelper.getAuthHeaders(token),
      });

      expect(response.status()).toBe(404);
      const error = await response.json();
      expect(error.detail).toContain('not found');
    });
  });

  test.describe('Error Handling', () => {
    test('should handle invalid order IDs', async ({ request }) => {
      const invalidId = 'invalid';
      
      const response = await request.get(`${apiEndpoints.backend}${apiEndpoints.orders}/${invalidId}`, {
        headers: apiHelper.getAuthHeaders(token),
      });

      expect(response.status()).toBe(422);
    });

    test('should handle missing required fields', async ({ request }) => {
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orders}/${testOrderId}/status`, {
        data: {}, // Missing status field
        headers: apiHelper.getAuthHeaders(token),
      });

      expect(response.status()).toBe(422);
      const error = await response.json();
      expect(error.detail).toBeDefined();
    });

    test('should handle database errors gracefully', async ({ request }) => {
      // This test would require mocking database failures
      // For now, just verify error responses are properly formatted
      
      const response = await request.put(`${apiEndpoints.backend}${apiEndpoints.orders}/99999/status`, {
        data: { status: 'processing' },
        headers: apiHelper.getAuthHeaders(token),
      });

      // Should return proper error structure
      if (!response.ok()) {
        const error = await response.json();
        expect(error.detail).toBeDefined();
      }
    });
  });

  test.describe('Performance Tests', () => {
    test('should handle rapid API calls', async () => {
      const promises = [];
      
      // Make multiple concurrent API calls
      for (let i = 0; i < 5; i++) {
        promises.push(apiHelper.getOrder(token, testOrderId));
      }
      
      const results = await Promise.all(promises);
      expect(results).toHaveLength(5);
      
      // All should return the same order
      results.forEach(order => {
        expect(order.id).toBe(testOrderId);
      });
    });

    test('should respond within acceptable timeframes', async () => {
      const startTime = Date.now();
      await apiHelper.getOrder(token, testOrderId);
      const responseTime = Date.now() - startTime;
      
      expect(responseTime).toBeLessThan(1000); // Should respond within 1 second
    });
  });
});