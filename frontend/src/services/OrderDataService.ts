import { ordersAPI } from './api';
import type { Order, OrderNote } from '../types';

export interface IOrderDataService {
  fetchOrders(accountId: number, status?: string): Promise<Order[]>;
  updateOrderStatus(orderId: number, status: string): Promise<void>;
  updateTrackingNumber(orderId: number, trackingNumber: string): Promise<void>;
  addOrderNote(orderId: number, note: string): Promise<OrderNote>;
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

  async updateTrackingNumber(orderId: number, trackingNumber: string): Promise<void> {
    try {
      await ordersAPI.updateTrackingNumber(orderId, trackingNumber);
    } catch (error) {
      console.error('Failed to update tracking number:', error);
      throw error;
    }
  }

  async addOrderNote(orderId: number, note: string): Promise<OrderNote> {
    try {
      return await ordersAPI.addOrderNote(orderId, note);
    } catch (error) {
      console.error('Failed to add order note:', error);
      throw error;
    }
  }
}

export default new OrderDataService();