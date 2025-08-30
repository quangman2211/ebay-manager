import { ordersAPI } from './api';
import type { Order } from '../types';

export interface IOrderDataService {
  fetchOrders(accountId: number, status?: string): Promise<Order[]>;
  updateOrderStatus(orderId: number, status: string): Promise<void>;
}

class OrderDataService implements IOrderDataService {
  async fetchOrders(accountId: number, status?: string): Promise<Order[]> {
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
}

export default new OrderDataService();