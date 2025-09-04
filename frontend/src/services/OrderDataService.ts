import { ordersAPI } from './api';
import type { Order, BulkOperationResult } from '../types';

export interface IOrderDataService {
  fetchOrders(accountId?: number, status?: string): Promise<Order[]>;
  updateOrderStatus(orderId: number, status: string): Promise<void>;
  bulkUpdateOrderStatus(orderIds: number[], status: string): Promise<BulkOperationResult>;
  bulkUpdateOrderStatusWithAudit(orderIds: number[], status: string, userId: number): Promise<BulkOperationResult>;
}

class OrderDataService implements IOrderDataService {
  async fetchOrders(accountId?: number, status?: string): Promise<Order[]> {
    try {
      return await ordersAPI.getOrders(accountId, status);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      throw error;
    }
  }

  async updateOrderStatus(orderId: number, status: string): Promise<void> {
    try {
      await ordersAPI.updateOrderStatus(orderId, status);
    } catch (error) {
      console.error('Failed to update order status:', error);
      throw error;
    }
  }

  private validateBulkOperation(orderIds: number[], status: string): void {
    if (!orderIds || orderIds.length === 0) {
      throw new Error('Order IDs cannot be empty');
    }
    
    if (!status || status.trim() === '') {
      throw new Error('Status cannot be empty');
    }

    if (orderIds.length > 100) {
      throw new Error('Maximum batch size is 100 orders');
    }

    const validStatuses = ['pending', 'processing', 'shipped', 'completed'];
    if (!validStatuses.includes(status)) {
      throw new Error('Invalid status value');
    }
  }

  async bulkUpdateOrderStatus(orderIds: number[], status: string): Promise<BulkOperationResult> {
    this.validateBulkOperation(orderIds, status);
    
    let retryCount = 0;
    const maxRetries = 1;

    while (retryCount <= maxRetries) {
      try {
        const result = await ordersAPI.bulkUpdateOrderStatus(orderIds, status);
        return result;
      } catch (error) {
        retryCount++;
        if (retryCount > maxRetries) {
          console.error('Failed to bulk update order status:', error);
          throw error;
        }
        // Wait 1 second before retry
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    throw new Error('Max retries exceeded');
  }

  async bulkUpdateOrderStatusWithAudit(
    orderIds: number[], 
    status: string, 
    userId: number
  ): Promise<BulkOperationResult> {
    this.validateBulkOperation(orderIds, status);
    
    try {
      const auditContext = { userId, operation: 'bulk_status_update' };
      const result = await ordersAPI.bulkUpdateOrderStatus(orderIds, status, auditContext);
      return result;
    } catch (error) {
      console.error('Failed to bulk update order status with audit:', error);
      throw error;
    }
  }
}

export default new OrderDataService();