import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TrackingNumberInput from '../TrackingNumberInput';
import OrderDataService from '../../../services/OrderDataService';
import type { Order } from '../../../types';

// Mock the OrderDataService
jest.mock('../../../services/OrderDataService');
const mockOrderDataService = OrderDataService as jest.Mocked<typeof OrderDataService>;

const mockOrderWithTracking: Order = {
  id: 1,
  item_id: 'test-item-1',
  account_id: 1,
  created_at: '2025-08-31T00:00:00Z',
  csv_row: {
    'Order Number': 'ORD-123456',
    'Tracking Number': '1Z123456789012345',
  },
};

const mockOrderWithoutTracking: Order = {
  id: 2,
  item_id: 'test-item-2',
  account_id: 1,
  created_at: '2025-08-31T00:00:00Z',
  csv_row: {
    'Order Number': 'ORD-654321',
  },
};

describe('TrackingNumberInput', () => {
  const defaultProps = {
    order: mockOrderWithTracking,
    onTrackingUpdate: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays existing tracking number', () => {
    render(<TrackingNumberInput {...defaultProps} />);
    
    expect(screen.getByText('1Z123456789012345')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument(); // Edit button
  });

  it('displays "No tracking" when no tracking number exists', () => {
    render(<TrackingNumberInput order={mockOrderWithoutTracking} onTrackingUpdate={jest.fn()} />);
    
    expect(screen.getByText('No tracking')).toBeInTheDocument();
  });

  it('enters edit mode when edit button is clicked', () => {
    render(<TrackingNumberInput {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1Z123456789012345')).toBeInTheDocument();
  });

  it('cancels edit mode when cancel button is clicked', () => {
    render(<TrackingNumberInput {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const cancelButton = screen.getByLabelText(/cancel/i);
    fireEvent.click(cancelButton);
    
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.getByText('1Z123456789012345')).toBeInTheDocument();
  });

  it('updates tracking number successfully', async () => {
    mockOrderDataService.updateTrackingNumber.mockResolvedValue();
    
    render(<TrackingNumberInput {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: '1Z999888777666555' } });
    
    const saveButton = screen.getByLabelText(/save/i);
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockOrderDataService.updateTrackingNumber).toHaveBeenCalledWith(1, '1Z999888777666555');
      expect(defaultProps.onTrackingUpdate).toHaveBeenCalledWith(1, '1Z999888777666555');
    });
  });

  it('validates tracking number format', async () => {
    render(<TrackingNumberInput {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: '123' } }); // Invalid format
    
    const saveButton = screen.getByLabelText(/save/i);
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Invalid tracking number format/)).toBeInTheDocument();
    });
    
    expect(mockOrderDataService.updateTrackingNumber).not.toHaveBeenCalled();
  });

  it('handles update errors gracefully', async () => {
    mockOrderDataService.updateTrackingNumber.mockRejectedValue(new Error('Network error'));
    
    render(<TrackingNumberInput {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: '1Z999888777666555' } });
    
    const saveButton = screen.getByLabelText(/save/i);
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to update tracking number/)).toBeInTheDocument();
    });
  });

  it('accepts valid UPS tracking numbers', async () => {
    mockOrderDataService.updateTrackingNumber.mockResolvedValue();
    
    render(<TrackingNumberInput {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: '1Z123456789012345678' } }); // Valid UPS format
    
    const saveButton = screen.getByLabelText(/save/i);
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockOrderDataService.updateTrackingNumber).toHaveBeenCalled();
    });
  });

  it('accepts valid USPS tracking numbers', async () => {
    mockOrderDataService.updateTrackingNumber.mockResolvedValue();
    
    render(<TrackingNumberInput {...defaultProps} />);
    
    const editButton = screen.getByRole('button');
    fireEvent.click(editButton);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: '9405511206213849632045' } }); // Valid USPS format
    
    const saveButton = screen.getByLabelText(/save/i);
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockOrderDataService.updateTrackingNumber).toHaveBeenCalled();
    });
  });
});