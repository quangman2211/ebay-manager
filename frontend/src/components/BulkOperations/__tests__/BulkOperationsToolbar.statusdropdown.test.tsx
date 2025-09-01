import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import BulkOperationsToolbar from '../BulkOperationsToolbar';
import type { Order } from '../../../types';

// Mock orders with different statuses
const mockOrdersPending: Order[] = [
  {
    id: 1,
    item_id: 'ORDER-001',
    order_status: { status: 'pending' },
    csv_row: { 'Order Number': 'ORDER-001' }
  },
  {
    id: 2,
    item_id: 'ORDER-002', 
    order_status: { status: 'pending' },
    csv_row: { 'Order Number': 'ORDER-002' }
  },
];

const mockOrdersMixed: Order[] = [
  {
    id: 1,
    item_id: 'ORDER-001',
    order_status: { status: 'pending' },
    csv_row: { 'Order Number': 'ORDER-001' }
  },
  {
    id: 2,
    item_id: 'ORDER-002',
    order_status: { status: 'processing' },
    csv_row: { 'Order Number': 'ORDER-002' }
  },
  {
    id: 3,
    item_id: 'ORDER-003',
    order_status: { status: 'shipped' },
    csv_row: { 'Order Number': 'ORDER-003' }
  },
];

const defaultProps = {
  onBulkUpdate: jest.fn(),
  onClearSelection: jest.fn(),
  loading: false,
};

describe('BulkOperationsToolbar Status Dropdown Fix', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Status dropdown options - Same status orders', () => {
    it('should show valid transitions for pending orders', () => {
      render(
        <BulkOperationsToolbar
          {...defaultProps}
          selectedOrders={mockOrdersPending}
        />
      );

      // Click on the status dropdown
      const statusSelect = screen.getByLabelText('New Status');
      fireEvent.mouseDown(statusSelect);

      // Should show valid transitions for pending: processing, shipped
      expect(screen.getByText('Processing')).toBeInTheDocument();
      expect(screen.getByText('Shipped')).toBeInTheDocument();
      
      // Should not show pending or completed
      expect(screen.queryByText('Pending')).not.toBeInTheDocument();
      expect(screen.queryByText('Completed')).not.toBeInTheDocument();
    });
  });

  describe('Status dropdown options - Mixed status orders (bug fix)', () => {
    it('should show all status options for mixed status selection', () => {
      render(
        <BulkOperationsToolbar
          {...defaultProps}
          selectedOrders={mockOrdersMixed}
        />
      );

      // Click on the status dropdown
      const statusSelect = screen.getByLabelText('New Status');
      fireEvent.mouseDown(statusSelect);

      // For mixed statuses, should show ALL status options to allow flexible bulk updates
      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('Processing')).toBeInTheDocument();
      expect(screen.getByText('Shipped')).toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument();
    });

    it('should enable the update button when status is selected for mixed orders', () => {
      render(
        <BulkOperationsToolbar
          {...defaultProps}
          selectedOrders={mockOrdersMixed}
        />
      );

      // Initially, update button should be disabled
      const updateButton = screen.getByText('Update Status');
      expect(updateButton).toBeDisabled();

      // Select a status
      const statusSelect = screen.getByLabelText('New Status');
      fireEvent.mouseDown(statusSelect);
      
      const completedOption = screen.getByText('Completed');
      fireEvent.click(completedOption);

      // Now update button should be enabled
      expect(updateButton).toBeEnabled();
    });

    it('should show correct count for mixed status selection', () => {
      render(
        <BulkOperationsToolbar
          {...defaultProps}
          selectedOrders={mockOrdersMixed}
        />
      );

      // Should show correct count
      expect(screen.getByText('3 orders selected')).toBeInTheDocument();
    });
  });

  describe('Empty selection behavior', () => {
    it('should not show any status options when no orders selected', () => {
      render(
        <BulkOperationsToolbar
          {...defaultProps}
          selectedOrders={[]}
        />
      );

      // Status dropdown should be disabled (check aria-disabled)
      const statusSelect = screen.getByLabelText('New Status');
      expect(statusSelect).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('Edge cases', () => {
    it('should handle orders without status gracefully', () => {
      const ordersWithoutStatus: Order[] = [
        {
          id: 1,
          item_id: 'ORDER-001',
          csv_row: { 'Order Number': 'ORDER-001' }
          // No order_status property
        } as Order,
      ];

      render(
        <BulkOperationsToolbar
          {...defaultProps}
          selectedOrders={ordersWithoutStatus}
        />
      );

      // Should default to 'pending' and show valid transitions
      const statusSelect = screen.getByLabelText('New Status');
      fireEvent.mouseDown(statusSelect);

      expect(screen.getByText('Processing')).toBeInTheDocument();
      expect(screen.getByText('Shipped')).toBeInTheDocument();
    });

    it('should handle completed orders correctly', () => {
      const completedOrders: Order[] = [
        {
          id: 1,
          item_id: 'ORDER-001',
          order_status: { status: 'completed' },
          csv_row: { 'Order Number': 'ORDER-001' }
        },
      ];

      render(
        <BulkOperationsToolbar
          {...defaultProps}
          selectedOrders={completedOrders}
        />
      );

      // Completed orders have no valid transitions, so dropdown should be empty
      const statusSelect = screen.getByLabelText('New Status');
      fireEvent.mouseDown(statusSelect);

      // Should not show any options
      expect(screen.queryByText('Pending')).not.toBeInTheDocument();
      expect(screen.queryByText('Processing')).not.toBeInTheDocument();
      expect(screen.queryByText('Shipped')).not.toBeInTheDocument();
      expect(screen.queryByText('Completed')).not.toBeInTheDocument();
    });
  });
});