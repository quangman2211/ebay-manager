import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import OrderDetailModal from '../OrderDetailModal';
import type { Order } from '../../../types';

const mockOrder: Order = {
  id: 1,
  item_id: 'test-item-1',
  account_id: 1,
  created_at: '2025-08-31T00:00:00Z',
  csv_row: {
    'Order Number': 'ORD-123456',
    'Item Number': 'ITM-789',
    'Item Title': 'Test Product',
    'Buyer Name': 'John Doe',
    'Buyer Username': 'johndoe123',
    'Buyer Email': 'john@example.com',
    'Ship To Address 1': '123 Main St',
    'Ship To City': 'New York',
    'Ship To State': 'NY',
    'Ship To Zip': '10001',
    'Ship To Phone': '555-0123',
    'Sold For': '$29.99',
    'Tracking Number': '1Z123456789',
    'Sale Date': '2025-08-30',
    'Ship By Date': '2025-09-02',
  },
  order_status: {
    id: 1,
    csv_data_id: 1,
    status: 'processing',
    updated_by: 1,
    updated_at: '2025-08-31T00:00:00Z',
  },
  notes: [
    {
      id: 1,
      order_id: 1,
      note: 'Customer requested expedited shipping',
      created_by: 1,
      created_at: '2025-08-31T00:00:00Z',
    }
  ],
};

describe('OrderDetailModal', () => {
  const defaultProps = {
    order: mockOrder,
    open: true,
    onClose: jest.fn(),
    onNotesUpdate: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders order details when open', () => {
    render(<OrderDetailModal {...defaultProps} />);
    
    expect(screen.getByText('Order Details')).toBeInTheDocument();
    expect(screen.getByText('ORD-123456')).toBeInTheDocument();
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('123 Main St')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<OrderDetailModal {...defaultProps} open={false} />);
    
    expect(screen.queryByText('Order Details')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<OrderDetailModal {...defaultProps} />);
    
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('displays order status correctly', () => {
    render(<OrderDetailModal {...defaultProps} />);
    
    expect(screen.getByText('Processing')).toBeInTheDocument();
  });

  it('shows order history timeline', () => {
    render(<OrderDetailModal {...defaultProps} />);
    
    expect(screen.getByText('Order History')).toBeInTheDocument();
  });

  it('shows order notes section when onNotesUpdate is provided', () => {
    render(<OrderDetailModal {...defaultProps} />);
    
    expect(screen.getByText('Order Notes')).toBeInTheDocument();
    expect(screen.getByText('Customer requested expedited shipping')).toBeInTheDocument();
  });

  it('does not show notes section when onNotesUpdate is not provided', () => {
    const { onNotesUpdate, ...propsWithoutCallback } = defaultProps;
    render(<OrderDetailModal {...propsWithoutCallback} />);
    
    expect(screen.queryByText('Order Notes')).not.toBeInTheDocument();
  });

  it('handles null order gracefully', () => {
    render(<OrderDetailModal {...defaultProps} order={null} />);
    
    expect(screen.getByText('Order Details')).toBeInTheDocument();
    expect(screen.queryByText('ORD-123456')).not.toBeInTheDocument();
  });
});