import { ordersAPI } from '../api';
import OrderDataService, { IOrderDataService } from '../OrderDataService';
import type { Order, BulkOperationResult } from '../../types';

// Mock the API module
jest.mock('../api', () => ({
  ordersAPI: {
    getOrders: jest.fn(),
    updateOrderStatus: jest.fn(),
    bulkUpdateOrderStatus: jest.fn(),
  },
}));

const mockOrdersAPI = ordersAPI as jest.Mocked<typeof ordersAPI>;

describe('OrderDataService - Bulk Operations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('bulkUpdateOrderStatus', () => {
    it('should successfully update multiple orders status', async () => {
      // Arrange
      const orderIds = [1, 2, 3];
      const newStatus = 'shipped';
      const mockResult: BulkOperationResult = {
        successful: orderIds,
        failed: [],
        totalProcessed: 3,
        errors: [],
      };

      mockOrdersAPI.bulkUpdateOrderStatus.mockResolvedValue(mockResult);

      // Act
      const result = await OrderDataService.bulkUpdateOrderStatus(orderIds, newStatus);

      // Assert
      expect(mockOrdersAPI.bulkUpdateOrderStatus).toHaveBeenCalledWith(orderIds, newStatus);
      expect(result).toEqual(mockResult);
      expect(result.successful.length).toBe(3);
      expect(result.failed.length).toBe(0);
    });

    it('should handle partial failures in bulk update', async () => {
      // Arrange
      const orderIds = [1, 2, 3, 4];
      const newStatus = 'processing';
      const mockResult: BulkOperationResult = {
        successful: [1, 2, 4],
        failed: [3],
        totalProcessed: 4,
        errors: ['Order 3: Invalid status transition'],
      };

      mockOrdersAPI.bulkUpdateOrderStatus.mockResolvedValue(mockResult);

      // Act
      const result = await OrderDataService.bulkUpdateOrderStatus(orderIds, newStatus);

      // Assert
      expect(result.successful.length).toBe(3);
      expect(result.failed.length).toBe(1);
      expect(result.failed).toContain(3);
      expect(result.errors).toContain('Order 3: Invalid status transition');
    });

    it('should throw error when bulk update fails completely', async () => {
      // Arrange
      const orderIds = [1, 2];
      const newStatus = 'shipped';
      const mockError = new Error('Network error');

      mockOrdersAPI.bulkUpdateOrderStatus.mockRejectedValue(mockError);

      // Act & Assert
      await expect(
        OrderDataService.bulkUpdateOrderStatus(orderIds, newStatus)
      ).rejects.toThrow('Network error');
    });

    it('should validate order IDs are not empty', async () => {
      // Arrange
      const orderIds: number[] = [];
      const newStatus = 'shipped';

      // Act & Assert
      await expect(
        OrderDataService.bulkUpdateOrderStatus(orderIds, newStatus)
      ).rejects.toThrow('Order IDs cannot be empty');
    });

    it('should validate status is provided', async () => {
      // Arrange
      const orderIds = [1, 2];
      const newStatus = '';

      // Act & Assert
      await expect(
        OrderDataService.bulkUpdateOrderStatus(orderIds, newStatus)
      ).rejects.toThrow('Status cannot be empty');
    });
  });

  describe('validateBulkOperation', () => {
    it('should validate maximum batch size', async () => {
      // Arrange
      const orderIds = Array.from({ length: 101 }, (_, i) => i + 1); // 101 orders
      const newStatus = 'shipped';

      // Act & Assert
      await expect(
        OrderDataService.bulkUpdateOrderStatus(orderIds, newStatus)
      ).rejects.toThrow('Maximum batch size is 100 orders');
    });

    it('should validate valid status values', async () => {
      // Arrange
      const orderIds = [1, 2];
      const invalidStatus = 'invalid-status';

      // Act & Assert
      await expect(
        OrderDataService.bulkUpdateOrderStatus(orderIds, invalidStatus)
      ).rejects.toThrow('Invalid status value');
    });
  });

  describe('Performance and Reliability', () => {
    it('should handle large batch of orders efficiently', async () => {
      // Arrange
      const orderIds = Array.from({ length: 100 }, (_, i) => i + 1);
      const newStatus = 'processing';
      const mockResult: BulkOperationResult = {
        successful: orderIds,
        failed: [],
        totalProcessed: 100,
        errors: [],
      };

      mockOrdersAPI.bulkUpdateOrderStatus.mockResolvedValue(mockResult);
      
      const startTime = Date.now();

      // Act
      const result = await OrderDataService.bulkUpdateOrderStatus(orderIds, newStatus);
      
      const endTime = Date.now();
      const executionTime = endTime - startTime;

      // Assert
      expect(result.successful.length).toBe(100);
      expect(executionTime).toBeLessThan(5000); // Should complete within 5 seconds
    });

    it('should retry failed operations once', async () => {
      // Arrange
      const orderIds = [1, 2];
      const newStatus = 'shipped';
      
      mockOrdersAPI.bulkUpdateOrderStatus
        .mockRejectedValueOnce(new Error('Temporary network error'))
        .mockResolvedValueOnce({
          successful: [1, 2],
          failed: [],
          totalProcessed: 2,
          errors: [],
        });

      // Act
      const result = await OrderDataService.bulkUpdateOrderStatus(orderIds, newStatus);

      // Assert
      expect(mockOrdersAPI.bulkUpdateOrderStatus).toHaveBeenCalledTimes(2);
      expect(result.successful.length).toBe(2);
    });
  });

  describe('Audit Trail', () => {
    it('should include user context in bulk operations', async () => {
      // Arrange
      const orderIds = [1, 2];
      const newStatus = 'shipped';
      const userId = 123;
      const mockResult: BulkOperationResult = {
        successful: orderIds,
        failed: [],
        totalProcessed: 2,
        errors: [],
        audit: {
          userId,
          timestamp: new Date().toISOString(),
          operation: 'bulk_status_update',
        },
      };

      mockOrdersAPI.bulkUpdateOrderStatus.mockResolvedValue(mockResult);

      // Act
      const result = await OrderDataService.bulkUpdateOrderStatusWithAudit(
        orderIds, 
        newStatus, 
        userId
      );

      // Assert
      expect(mockOrdersAPI.bulkUpdateOrderStatus).toHaveBeenCalledWith(
        orderIds, 
        newStatus, 
        { userId, operation: 'bulk_status_update' }
      );
      expect(result.audit?.userId).toBe(userId);
      expect(result.audit?.operation).toBe('bulk_status_update');
    });
  });
});