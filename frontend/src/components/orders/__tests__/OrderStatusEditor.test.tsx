import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import OrderStatusEditor from '../OrderStatusEditor';
import OrderDataService from '../../../services/OrderDataService';
import type { Order } from '../../../types';

// Mock the OrderDataService
jest.mock('../../../services/OrderDataService');
const mockOrderDataService = OrderDataService as jest.Mocked<typeof OrderDataService>;

const mockOrder: Order = {
  id: 1,
  item_id: 'test-item-1',
  account_id: 1,
  created_at: '2025-08-31T00:00:00Z',
  csv_row: {
    'Order Number': 'ORD-123456',
  },
  order_status: {
    id: 1,
    csv_data_id: 1,
    status: 'pending',
    updated_by: 1,
    updated_at: '2025-08-31T00:00:00Z',
  },
};

describe('OrderStatusEditor', () => {
  const defaultProps = {
    order: mockOrder,
    onStatusUpdate: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays current status as chip', () => {
    render(<OrderStatusEditor {...defaultProps} />);
    
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument(); // Edit button
  });

  it('enters edit mode when edit button is clicked', () => {
    render(<OrderStatusEditor {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    expect(screen.getByRole('combobox')).toBeInTheDocument(); // Select dropdown
    expect(screen.getByLabelText(/save/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/cancel/i)).toBeInTheDocument();
  });

  it('shows valid status transitions only', () => {
    render(<OrderStatusEditor {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText('Processing')).toBeInTheDocument();
    expect(screen.queryByText('Completed')).not.toBeInTheDocument(); // Invalid transition
  });

  it('cancels edit mode when cancel button is clicked', () => {
    render(<OrderStatusEditor {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const cancelButton = screen.getByLabelText(/cancel/i);
    fireEvent.click(cancelButton);
    
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('updates status successfully', async () => {
    mockOrderDataService.updateOrderStatus.mockResolvedValue();
    
    render(<OrderStatusEditor {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getByText('Processing'));
    
    const saveButton = screen.getByLabelText(/save/i);
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockOrderDataService.updateOrderStatus).toHaveBeenCalledWith(1, 'processing');
      expect(defaultProps.onStatusUpdate).toHaveBeenCalledWith(1, 'processing');
    });
  });

  it('handles update errors gracefully', async () => {
    mockOrderDataService.updateOrderStatus.mockRejectedValue(new Error('Network error'));
    
    render(<OrderStatusEditor {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    fireEvent.click(screen.getByText('Processing'));
    
    const saveButton = screen.getByLabelText(/save/i);
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to update order status/)).toBeInTheDocument();
    });
  });

  it('validates status transitions', () => {
    const completedOrder = {
      ...mockOrder,
      order_status: {
        ...mockOrder.order_status!,
        status: 'completed' as const,
      },
    };
    
    render(<OrderStatusEditor order={completedOrder} onStatusUpdate={jest.fn()} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const select = screen.getByRole('combobox');
    fireEvent.mouseDown(select);
    
    // Completed orders should only show "Completed" option
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.queryByText('Processing')).not.toBeInTheDocument();
  });
});