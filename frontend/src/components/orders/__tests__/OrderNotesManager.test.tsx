import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import OrderNotesManager from '../OrderNotesManager';
import OrderDataService from '../../../services/OrderDataService';
import type { Order, OrderNote } from '../../../types';

// Mock the OrderDataService
jest.mock('../../../services/OrderDataService');
const mockOrderDataService = OrderDataService as jest.Mocked<typeof OrderDataService>;

const mockNote: OrderNote = {
  id: 1,
  order_id: 1,
  note: 'Customer requested expedited shipping',
  created_by: 1,
  created_at: '2025-08-31T00:00:00Z',
};

const mockOrderWithNotes: Order = {
  id: 1,
  item_id: 'test-item-1',
  account_id: 1,
  created_at: '2025-08-31T00:00:00Z',
  csv_row: {
    'Order Number': 'ORD-123456',
  },
  notes: [mockNote],
};

const mockOrderWithoutNotes: Order = {
  id: 2,
  item_id: 'test-item-2',
  account_id: 1,
  created_at: '2025-08-31T00:00:00Z',
  csv_row: {
    'Order Number': 'ORD-654321',
  },
  notes: [],
};

describe('OrderNotesManager', () => {
  const defaultProps = {
    order: mockOrderWithNotes,
    onNotesUpdate: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays existing notes', () => {
    render(<OrderNotesManager {...defaultProps} />);
    
    expect(screen.getByText('Order Notes')).toBeInTheDocument();
    expect(screen.getByText('Customer requested expedited shipping')).toBeInTheDocument();
  });

  it('shows "No notes" message when no notes exist', () => {
    render(<OrderNotesManager order={mockOrderWithoutNotes} onNotesUpdate={jest.fn()} />);
    
    expect(screen.getByText('No notes added yet')).toBeInTheDocument();
  });

  it('displays add note form', () => {
    render(<OrderNotesManager {...defaultProps} />);
    
    expect(screen.getByText('Add New Note')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Add a note about this order...')).toBeInTheDocument();
    expect(screen.getByText('Add Note')).toBeInTheDocument();
  });

  it('adds new note successfully', async () => {
    const newNote = {
      id: 2,
      order_id: 1,
      note: 'Order shipped early',
      created_by: 1,
      created_at: '2025-08-31T01:00:00Z',
    };
    
    mockOrderDataService.addOrderNote.mockResolvedValue(newNote);
    
    render(<OrderNotesManager {...defaultProps} />);
    
    const textarea = screen.getByPlaceholderText('Add a note about this order...');
    fireEvent.change(textarea, { target: { value: 'Order shipped early' } });
    
    const addButton = screen.getByText('Add Note');
    fireEvent.click(addButton);
    
    await waitFor(() => {
      expect(mockOrderDataService.addOrderNote).toHaveBeenCalledWith(1, 'Order shipped early');
      expect(defaultProps.onNotesUpdate).toHaveBeenCalledWith(1, [mockNote, newNote]);
    });
  });

  it('validates note content', async () => {
    render(<OrderNotesManager {...defaultProps} />);
    
    const textarea = screen.getByPlaceholderText('Add a note about this order...');
    fireEvent.change(textarea, { target: { value: 'x' } }); // Too short
    
    const addButton = screen.getByText('Add Note');
    fireEvent.click(addButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Note must be at least 3 characters/)).toBeInTheDocument();
    });
    
    expect(mockOrderDataService.addOrderNote).not.toHaveBeenCalled();
  });

  it('prevents adding empty notes', () => {
    render(<OrderNotesManager {...defaultProps} />);
    
    const addButton = screen.getByText('Add Note');
    expect(addButton).toBeDisabled();
  });

  it('shows character count', () => {
    render(<OrderNotesManager {...defaultProps} />);
    
    expect(screen.getByText('0/500 characters')).toBeInTheDocument();
    
    const textarea = screen.getByPlaceholderText('Add a note about this order...');
    fireEvent.change(textarea, { target: { value: 'Test note' } });
    
    expect(screen.getByText('9/500 characters')).toBeInTheDocument();
  });

  it('handles add note errors gracefully', async () => {
    mockOrderDataService.addOrderNote.mockRejectedValue(new Error('Network error'));
    
    render(<OrderNotesManager {...defaultProps} />);
    
    const textarea = screen.getByPlaceholderText('Add a note about this order...');
    fireEvent.change(textarea, { target: { value: 'Valid note content' } });
    
    const addButton = screen.getByText('Add Note');
    fireEvent.click(addButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to add note/)).toBeInTheDocument();
    });
  });
});