/**
 * Order management configuration constants
 * Centralized to eliminate hardcoded values (SOLID compliance)
 */

export const ORDER_STATUSES = {
  PENDING: 'pending',
  PROCESSING: 'processing', 
  SHIPPED: 'shipped',
  COMPLETED: 'completed',
} as const;

export type OrderStatus = typeof ORDER_STATUSES[keyof typeof ORDER_STATUSES];

export const VALID_ORDER_STATUSES: OrderStatus[] = Object.values(ORDER_STATUSES);

export const STATUS_TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  [ORDER_STATUSES.PENDING]: [ORDER_STATUSES.PROCESSING, ORDER_STATUSES.SHIPPED],
  [ORDER_STATUSES.PROCESSING]: [ORDER_STATUSES.SHIPPED, ORDER_STATUSES.COMPLETED],
  [ORDER_STATUSES.SHIPPED]: [ORDER_STATUSES.COMPLETED],
  [ORDER_STATUSES.COMPLETED]: [],
};

export const BULK_OPERATION_CONFIG = {
  MAX_BATCH_SIZE: 100,
  DEFAULT_RETRY_COUNT: 1,
  RETRY_DELAY_MS: 1000,
  OPERATION_TIMEOUT_MS: 5000,
} as const;

export const getStatusLabel = (status: OrderStatus): string => {
  const labels: Record<OrderStatus, string> = {
    [ORDER_STATUSES.PENDING]: 'Pending',
    [ORDER_STATUSES.PROCESSING]: 'Processing',
    [ORDER_STATUSES.SHIPPED]: 'Shipped',
    [ORDER_STATUSES.COMPLETED]: 'Completed',
  };
  
  return labels[status] || status;
};

export const isValidOrderStatus = (status: string): status is OrderStatus => {
  return VALID_ORDER_STATUSES.includes(status as OrderStatus);
};

export const getValidTransitions = (currentStatus: OrderStatus): OrderStatus[] => {
  return STATUS_TRANSITIONS[currentStatus] || [];
};