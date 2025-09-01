import { useState, useEffect, useCallback, useMemo } from 'react';
import type { Order } from '../types';

export interface BulkSelectionOptions {
  maxSelection?: number;
  onChange?: (selectedIds: number[], selectedOrders: Order[]) => void;
  onSelectionLimitReached?: (limit: number) => void;
}

export interface BulkSelectionResult {
  selectedOrderIds: number[];
  selectedOrders: Order[];
  isAllSelected: boolean;
  isIndeterminate: boolean;
  isSelectionLimitReached: boolean;
  toggleOrder: (orderId: number) => void;
  selectAll: () => void;
  clearSelection: () => void;
  toggleAll: () => void;
  selectByStatus: (status: string) => void;
  isOrderSelected: (orderId: number) => boolean;
}

export const useBulkSelection = (
  orders: Order[],
  options: BulkSelectionOptions = {}
): BulkSelectionResult => {
  const { maxSelection = Infinity, onChange, onSelectionLimitReached } = options;
  const [selectedOrderIds, setSelectedOrderIds] = useState<number[]>([]);

  // Update selection when orders list changes
  useEffect(() => {
    const validOrderIds = orders.map(order => order.id);
    setSelectedOrderIds(prev => prev.filter(id => validOrderIds.includes(id)));
  }, [orders]);

  // Memoized computed values for performance
  const selectedOrders = useMemo(() => {
    return orders.filter(order => selectedOrderIds.includes(order.id));
  }, [orders, selectedOrderIds]);

  const isAllSelected = useMemo(() => {
    return orders.length > 0 && selectedOrderIds.length === orders.length;
  }, [orders.length, selectedOrderIds.length]);

  const isIndeterminate = useMemo(() => {
    return selectedOrderIds.length > 0 && selectedOrderIds.length < orders.length;
  }, [orders.length, selectedOrderIds.length]);

  const isSelectionLimitReached = useMemo(() => {
    return selectedOrderIds.length >= maxSelection;
  }, [selectedOrderIds.length, maxSelection]);

  // Trigger onChange callback when selection changes
  useEffect(() => {
    if (onChange) {
      onChange(selectedOrderIds, selectedOrders);
    }
  }, [selectedOrderIds, selectedOrders, onChange]);

  const toggleOrder = useCallback((orderId: number) => {
    setSelectedOrderIds(prev => {
      if (prev.includes(orderId)) {
        // Remove from selection
        return prev.filter(id => id !== orderId);
      } else {
        // Add to selection if under limit
        if (prev.length >= maxSelection) {
          onSelectionLimitReached?.(maxSelection);
          return prev;
        }
        return [...prev, orderId];
      }
    });
  }, [maxSelection, onSelectionLimitReached]);

  const selectAll = useCallback(() => {
    const orderIds = orders.map(order => order.id);
    const limitedOrderIds = orderIds.slice(0, maxSelection);
    
    if (orderIds.length > maxSelection) {
      onSelectionLimitReached?.(maxSelection);
    }
    
    setSelectedOrderIds(limitedOrderIds);
  }, [orders, maxSelection, onSelectionLimitReached]);

  const clearSelection = useCallback(() => {
    setSelectedOrderIds([]);
  }, []);

  const toggleAll = useCallback(() => {
    if (isAllSelected) {
      clearSelection();
    } else {
      selectAll();
    }
  }, [isAllSelected, clearSelection, selectAll]);

  const selectByStatus = useCallback((status: string) => {
    const ordersWithStatus = orders.filter(
      order => order.order_status?.status === status
    );
    const orderIds = ordersWithStatus.map(order => order.id);
    const limitedOrderIds = orderIds.slice(0, maxSelection);
    
    if (orderIds.length > maxSelection) {
      onSelectionLimitReached?.(maxSelection);
    }
    
    setSelectedOrderIds(limitedOrderIds);
  }, [orders, maxSelection, onSelectionLimitReached]);

  const isOrderSelected = useCallback((orderId: number) => {
    return selectedOrderIds.includes(orderId);
  }, [selectedOrderIds]);

  return {
    selectedOrderIds,
    selectedOrders,
    isAllSelected,
    isIndeterminate,
    isSelectionLimitReached,
    toggleOrder,
    selectAll,
    clearSelection,
    toggleAll,
    selectByStatus,
    isOrderSelected,
  };
};