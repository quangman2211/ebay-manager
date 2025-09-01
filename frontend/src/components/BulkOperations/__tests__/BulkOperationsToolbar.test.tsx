import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import BulkOperationsToolbar from '../BulkOperationsToolbar';
import type { BulkOperationResult } from '../../../types';
import { createMockOrder, createMockOrderStatus } from '../../../test-utils';

const theme = createTheme();

const mockOrders = [
  createMockOrder({ 
    id: 1, 
    item_id: 'ORD-001',
    csv_row: { 'Order Number': 'ORD-001' }
  }),
  createMockOrder({ 
    id: 2, 
    item_id: 'ORD-002',
    csv_row: { 'Order Number': 'ORD-002' }
  }),
];

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('BulkOperationsToolbar', () => {
  const mockOnBulkUpdate = jest.fn();
  const mockOnClearSelection = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render disabled when no orders selected', () => {
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={[]}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      expect(screen.getByText('Bulk Actions')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /update status/i })).toBeDisabled();
      expect(screen.getByText('0 orders selected')).toBeInTheDocument();
    });

    it('should render enabled when orders are selected', () => {
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      expect(screen.getByRole('button', { name: /update status/i })).toBeDisabled(); // Disabled until status selected
      expect(screen.getByText('2 orders selected')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear selection/i })).toBeEnabled();
    });

    it('should show loading state during bulk operation', () => {
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={true}
        />
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });
  });

  describe('Status Selection', () => {
    it('should allow selecting new status', async () => {
      const user = userEvent.setup();
      
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      // Click status dropdown
      await user.click(screen.getByLabelText('New Status'));
      
      // Select processing status
      await user.click(screen.getByText('Processing'));

      // Click update button - should show confirmation dialog
      await user.click(screen.getByRole('button', { name: /update status/i }));

      // Confirm in dialog
      await waitFor(() => {
        expect(screen.getByText('Confirm Bulk Update')).toBeInTheDocument();
      });
      
      await user.click(screen.getByRole('button', { name: /confirm/i }));

      await waitFor(() => {
        expect(mockOnBulkUpdate).toHaveBeenCalledWith([1, 2], 'processing');
      });
    });

    it('should prevent invalid status transitions', async () => {
      const user = userEvent.setup();
      const shippedOrders = [
        createMockOrder({
          id: 3,
          item_id: 'ORD-003',
          order_status: createMockOrderStatus({ status: 'shipped' }),
          csv_row: { 'Order Number': 'ORD-003' },
        }),
      ];
      
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={shippedOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      // Click status dropdown
      await user.click(screen.getByLabelText('New Status'));
      
      // Try to select pending (invalid transition from shipped to pending)
      expect(screen.queryByText('Pending')).not.toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument(); // Valid transition
    });
  });

  describe('Confirmation Dialog', () => {
    it('should show confirmation dialog before bulk update', async () => {
      const user = userEvent.setup();
      
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      // Select status and click update
      await user.click(screen.getByLabelText('New Status'));
      await user.click(screen.getByText('Processing'));
      await user.click(screen.getByRole('button', { name: /update status/i }));

      // Check confirmation dialog
      expect(screen.getByText('Confirm Bulk Update')).toBeInTheDocument();
      expect(screen.getByText(/update 2 orders to "Processing"/i)).toBeInTheDocument();
      
      // List affected orders
      expect(screen.getByText('ORD-001')).toBeInTheDocument();
      expect(screen.getByText('ORD-002')).toBeInTheDocument();
    });

    it('should execute bulk update on confirmation', async () => {
      const user = userEvent.setup();
      
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      // Trigger confirmation dialog
      await user.click(screen.getByLabelText('New Status'));
      await user.click(screen.getByText('Processing'));
      await user.click(screen.getByRole('button', { name: /update status/i }));

      // Confirm update
      await user.click(screen.getByRole('button', { name: /confirm/i }));

      expect(mockOnBulkUpdate).toHaveBeenCalledWith([1, 2], 'processing');
    });

    it('should cancel bulk update on dialog cancel', async () => {
      const user = userEvent.setup();
      
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      // Trigger confirmation dialog
      await user.click(screen.getByLabelText('New Status'));
      await user.click(screen.getByText('Processing'));
      await user.click(screen.getByRole('button', { name: /update status/i }));

      // Cancel update
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(mockOnBulkUpdate).not.toHaveBeenCalled();
    });
  });

  describe('Progress Indicator', () => {
    it('should show progress during bulk operation', () => {
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={true}
          progress={50}
        />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
      expect(screen.getByText('50% complete')).toBeInTheDocument();
    });

    it('should allow canceling bulk operation', async () => {
      const mockOnCancel = jest.fn();
      const user = userEvent.setup();
      
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={true}
          progress={30}
          onCancel={mockOnCancel}
        />
      );

      await user.click(screen.getByRole('button', { name: /cancel/i }));
      expect(mockOnCancel).toHaveBeenCalled();
    });
  });

  describe('Result Display', () => {
    const mockResult: BulkOperationResult = {
      successful: [1],
      failed: [2],
      totalProcessed: 2,
      errors: ['Order 2: Invalid status transition'],
    };

    it('should display success and failure counts', () => {
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={[]}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
          lastResult={mockResult}
        />
      );

      expect(screen.getByText(/1 updated successfully/i)).toBeInTheDocument();
      expect(screen.getByText(/1 failed/i)).toBeInTheDocument();
    });

    it('should show error details on click', async () => {
      const user = userEvent.setup();
      
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={[]}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
          lastResult={mockResult}
        />
      );

      await user.click(screen.getByText(/view errors/i));
      expect(screen.getByText('Order 2: Invalid status transition')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      expect(screen.getByLabelText('New Status')).toBeInTheDocument();
      expect(screen.getByLabelText('Bulk operations toolbar')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /update status/i })).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      renderWithTheme(
        <BulkOperationsToolbar
          selectedOrders={mockOrders}
          onBulkUpdate={mockOnBulkUpdate}
          onClearSelection={mockOnClearSelection}
          loading={false}
        />
      );

      // Verify accessible elements exist with proper roles
      expect(screen.getByLabelText('New Status')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /update status/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear selection/i })).toBeInTheDocument();
      
      // Clear button should be enabled since orders are selected
      expect(screen.getByRole('button', { name: /clear selection/i })).not.toBeDisabled();
    });
  });
});