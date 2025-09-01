import type { Order, OrderStatus } from './types';

export function createMockOrderStatus(
  overrides: Partial<OrderStatus> = {}
): OrderStatus {
  return {
    id: 1,
    csv_data_id: 1,
    status: 'pending',
    updated_by: 1,
    updated_at: '2023-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createMockOrder(overrides: Partial<Order> = {}): Order {
  return {
    id: 1,
    account_id: 1,
    item_id: 'ORD-001',
    order_status: createMockOrderStatus(),
    csv_row: { 'Order Number': 'ORD-001' },
    created_at: '2023-01-01T00:00:00Z',
    ...overrides,
  };
}

export function createMockOrders(count: number): Order[] {
  return Array.from({ length: count }, (_, i) =>
    createMockOrder({
      id: i + 1,
      item_id: `ORD-${String(i + 1).padStart(3, '0')}`,
      order_status: createMockOrderStatus({
        id: i + 1,
        csv_data_id: i + 1,
      }),
      csv_row: { 'Order Number': `ORD-${String(i + 1).padStart(3, '0')}` },
    })
  );
}