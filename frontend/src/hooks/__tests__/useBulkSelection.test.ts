import { renderHook, act } from '@testing-library/react';
import { useBulkSelection } from '../useBulkSelection';
import { createMockOrder, createMockOrderStatus } from '../../test-utils';

const mockOrders = [
  createMockOrder({
    id: 1,
    item_id: 'ORD-001',
    order_status: createMockOrderStatus({ status: 'pending' }),
  }),
  createMockOrder({
    id: 2,
    item_id: 'ORD-002',
    order_status: createMockOrderStatus({ status: 'processing' }),
  }),
  createMockOrder({
    id: 3,
    item_id: 'ORD-003',
    order_status: createMockOrderStatus({ status: 'shipped' }),
  }),
];

describe('useBulkSelection', () => {
  describe('Selection Management', () => {
    it('should initialize with empty selection', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      expect(result.current.selectedOrderIds).toEqual([]);
      expect(result.current.selectedOrders).toEqual([]);
      expect(result.current.isAllSelected).toBe(false);
      expect(result.current.isIndeterminate).toBe(false);
    });

    it('should toggle single order selection', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      act(() => {
        result.current.toggleOrder(1);
      });

      expect(result.current.selectedOrderIds).toEqual([1]);
      expect(result.current.selectedOrders).toEqual([mockOrders[0]]);
      expect(result.current.isAllSelected).toBe(false);
      expect(result.current.isIndeterminate).toBe(true);
    });

    it('should deselect already selected order', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      act(() => {
        result.current.toggleOrder(1);
      });

      expect(result.current.selectedOrderIds).toEqual([1]);

      act(() => {
        result.current.toggleOrder(1);
      });

      expect(result.current.selectedOrderIds).toEqual([]);
      expect(result.current.isIndeterminate).toBe(false);
    });

    it('should handle multiple order selection', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      act(() => {
        result.current.toggleOrder(1);
        result.current.toggleOrder(2);
      });

      expect(result.current.selectedOrderIds).toEqual([1, 2]);
      expect(result.current.selectedOrders).toHaveLength(2);
      expect(result.current.isIndeterminate).toBe(true);
    });
  });

  describe('Select All Functionality', () => {
    it('should select all orders', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      act(() => {
        result.current.selectAll();
      });

      expect(result.current.selectedOrderIds).toEqual([1, 2, 3]);
      expect(result.current.selectedOrders).toHaveLength(3);
      expect(result.current.isAllSelected).toBe(true);
      expect(result.current.isIndeterminate).toBe(false);
    });

    it('should clear all selections', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      // First select all
      act(() => {
        result.current.selectAll();
      });

      expect(result.current.isAllSelected).toBe(true);

      // Then clear all
      act(() => {
        result.current.clearSelection();
      });

      expect(result.current.selectedOrderIds).toEqual([]);
      expect(result.current.isAllSelected).toBe(false);
      expect(result.current.isIndeterminate).toBe(false);
    });

    it('should toggle all when some orders are selected', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      // Select some orders first
      act(() => {
        result.current.toggleOrder(1);
        result.current.toggleOrder(2);
      });

      expect(result.current.isIndeterminate).toBe(true);

      // Toggle all should select remaining orders
      act(() => {
        result.current.toggleAll();
      });

      expect(result.current.isAllSelected).toBe(true);
      expect(result.current.selectedOrderIds).toEqual([1, 2, 3]);
    });

    it('should toggle all when all orders are selected', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      // Select all first
      act(() => {
        result.current.selectAll();
      });

      expect(result.current.isAllSelected).toBe(true);

      // Toggle all should clear selection
      act(() => {
        result.current.toggleAll();
      });

      expect(result.current.selectedOrderIds).toEqual([]);
      expect(result.current.isAllSelected).toBe(false);
    });
  });

  describe('Status-based Selection', () => {
    it('should select orders by status', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      act(() => {
        result.current.selectByStatus('pending');
      });

      expect(result.current.selectedOrderIds).toEqual([1]);
      expect(result.current.selectedOrders[0].order_status?.status).toBe('pending');
    });

    it('should handle empty status selection', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      act(() => {
        result.current.selectByStatus('completed'); // No orders with this status
      });

      expect(result.current.selectedOrderIds).toEqual([]);
    });

    it('should select multiple orders with same status', () => {
      const ordersWithSameStatus = [
        ...mockOrders,
        createMockOrder({
          id: 4,
          item_id: 'ORD-004',
          order_status: createMockOrderStatus({ status: 'pending' }),
        }),
      ];

      const { result } = renderHook(() => useBulkSelection(ordersWithSameStatus));

      act(() => {
        result.current.selectByStatus('pending');
      });

      expect(result.current.selectedOrderIds).toEqual([1, 4]);
    });
  });

  describe('Selection Validation', () => {
    it('should check if order is selected', () => {
      const { result } = renderHook(() => useBulkSelection(mockOrders));

      act(() => {
        result.current.toggleOrder(1);
      });

      expect(result.current.isOrderSelected(1)).toBe(true);
      expect(result.current.isOrderSelected(2)).toBe(false);
    });

    it('should validate selection limits', () => {
      const manyOrders = Array.from({ length: 150 }, (_, i) =>
        createMockOrder({
          id: i + 1,
          item_id: `ORD-${String(i + 1).padStart(3, '0')}`,
          order_status: createMockOrderStatus({ status: 'pending' }),
        })
      );

      const { result } = renderHook(() => useBulkSelection(manyOrders, { maxSelection: 100 }));

      act(() => {
        result.current.selectAll();
      });

      // Should only select first 100 orders due to limit
      expect(result.current.selectedOrderIds).toHaveLength(100);
      expect(result.current.isSelectionLimitReached).toBe(true);
    });
  });

  describe('Performance and Optimization', () => {
    it('should handle large datasets efficiently', () => {
      const largeOrderSet = Array.from({ length: 1000 }, (_, i) =>
        createMockOrder({
          id: i + 1,
          item_id: `ORD-${String(i + 1).padStart(4, '0')}`,
          order_status: createMockOrderStatus({
            status: i % 2 === 0 ? 'pending' : 'processing',
          }),
        })
      );

      const { result } = renderHook(() => useBulkSelection(largeOrderSet));

      const startTime = Date.now();

      act(() => {
        result.current.selectAll();
      });

      const endTime = Date.now();
      const executionTime = endTime - startTime;

      expect(result.current.selectedOrderIds).toHaveLength(1000);
      expect(executionTime).toBeLessThan(100); // Should complete within 100ms
    });

    it('should update selection when orders list changes', () => {
      let orders = mockOrders.slice(0, 2); // First 2 orders
      const { result, rerender } = renderHook(
        ({ orders }) => useBulkSelection(orders),
        { initialProps: { orders } }
      );

      act(() => {
        result.current.selectAll();
      });

      expect(result.current.selectedOrderIds).toEqual([1, 2]);

      // Update orders list (remove first order)
      orders = mockOrders.slice(1); // Orders 2 and 3
      rerender({ orders });

      // Selection should be updated to only include existing orders
      expect(result.current.selectedOrderIds).toEqual([2]);
      expect(result.current.selectedOrders).toHaveLength(1);
    });
  });

  describe('Event Callbacks', () => {
    it('should call onChange callback when selection changes', () => {
      const onChangeMock = jest.fn();
      const { result } = renderHook(() => 
        useBulkSelection(mockOrders, { onChange: onChangeMock })
      );

      act(() => {
        result.current.toggleOrder(1);
      });

      expect(onChangeMock).toHaveBeenCalledWith([1], [mockOrders[0]]);
    });

    it('should call onSelectionLimitReached when limit is exceeded', () => {
      const onLimitReachedMock = jest.fn();
      const { result } = renderHook(() => 
        useBulkSelection(mockOrders, { 
          maxSelection: 2,
          onSelectionLimitReached: onLimitReachedMock 
        })
      );

      act(() => {
        result.current.selectAll(); // Try to select 3 orders with limit of 2
      });

      expect(onLimitReachedMock).toHaveBeenCalledWith(2);
      expect(result.current.selectedOrderIds).toHaveLength(2);
    });
  });
});