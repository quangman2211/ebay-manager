import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ListingEditModal from '../ListingEditModal';
import { listingsAPI } from '../../../services/api';
import type { Listing } from '../../../types';

// Mock the API
jest.mock('../../../services/api');
const mockedListingsAPI = listingsAPI as jest.Mocked<typeof listingsAPI>;

// Mock listing data
const mockListing: Listing = {
  id: 1,
  item_id: '123456789',
  account_id: 1,
  created_at: '2024-01-01T00:00:00Z',
  csv_row: {
    'Title': 'Test Product',
    'Current price': '19.99',
    'Available quantity': '10',
    'Status': 'active',
    'Description': 'Test description'
  }
};

const mockMetrics = {
  sell_through_rate: 75.5,
  watchers_count: 12,
  stock_status: 'in_stock',
  days_listed: 45,
  price_competitiveness: 'competitive'
};

describe('ListingEditModal', () => {
  const defaultProps = {
    open: true,
    onClose: jest.fn(),
    listing: mockListing,
    onSave: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockedListingsAPI.getListingMetrics.mockResolvedValue(mockMetrics);
    mockedListingsAPI.updateListing.mockResolvedValue();
  });

  it('renders modal with listing data', async () => {
    render(<ListingEditModal {...defaultProps} />);

    expect(screen.getByText('Edit Listing - 123456789')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Product')).toBeInTheDocument();
    expect(screen.getByDisplayValue('19.99')).toBeInTheDocument();
    expect(screen.getByDisplayValue('10')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test description')).toBeInTheDocument();
  });

  it('loads and displays performance metrics', async () => {
    render(<ListingEditModal {...defaultProps} />);

    await waitFor(() => {
      expect(mockedListingsAPI.getListingMetrics).toHaveBeenCalledWith(1);
    });

    expect(screen.getByText('75.5%')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('IN STOCK')).toBeInTheDocument();
    expect(screen.getByText('COMPETITIVE')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    render(<ListingEditModal {...defaultProps} />);

    // Clear title field
    const titleField = screen.getByDisplayValue('Test Product');
    await user.clear(titleField);

    // Try to save
    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    expect(screen.getByText('Title is required')).toBeInTheDocument();
    expect(mockedListingsAPI.updateListing).not.toHaveBeenCalled();
  });

  it('validates price format', async () => {
    const user = userEvent.setup();
    render(<ListingEditModal {...defaultProps} />);

    const priceField = screen.getByDisplayValue('19.99');
    await user.clear(priceField);
    await user.type(priceField, 'invalid_price');

    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    expect(screen.getByText('Price must be a valid positive number')).toBeInTheDocument();
    expect(mockedListingsAPI.updateListing).not.toHaveBeenCalled();
  });

  it('validates quantity format', async () => {
    const user = userEvent.setup();
    render(<ListingEditModal {...defaultProps} />);

    const quantityField = screen.getByDisplayValue('10');
    await user.clear(quantityField);
    await user.type(quantityField, '-5');

    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    expect(screen.getByText('Quantity must be a valid non-negative number')).toBeInTheDocument();
    expect(mockedListingsAPI.updateListing).not.toHaveBeenCalled();
  });

  it('submits valid form data', async () => {
    const user = userEvent.setup();
    render(<ListingEditModal {...defaultProps} />);

    // Modify fields
    const titleField = screen.getByDisplayValue('Test Product');
    await user.clear(titleField);
    await user.type(titleField, 'Updated Product');

    const priceField = screen.getByDisplayValue('19.99');
    await user.clear(priceField);
    await user.type(priceField, '29.99');

    // Save changes
    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockedListingsAPI.updateListing).toHaveBeenCalledWith(1, {
        title: 'Updated Product',
        price: '29.99'
      });
    });

    expect(defaultProps.onSave).toHaveBeenCalled();
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup();
    mockedListingsAPI.updateListing.mockRejectedValue(new Error('API Error'));

    render(<ListingEditModal {...defaultProps} />);

    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Failed to update listing')).toBeInTheDocument();
    });

    expect(defaultProps.onSave).not.toHaveBeenCalled();
    expect(defaultProps.onClose).not.toHaveBeenCalled();
  });

  it('shows loading state during save', async () => {
    const user = userEvent.setup();
    // Mock a slow API call
    mockedListingsAPI.updateListing.mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 1000))
    );

    render(<ListingEditModal {...defaultProps} />);

    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    expect(screen.getByText('Saving...')).toBeInTheDocument();
    expect(saveButton).toBeDisabled();
  });

  it('closes modal when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(<ListingEditModal {...defaultProps} />);

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('does not submit if no changes made', async () => {
    const user = userEvent.setup();
    render(<ListingEditModal {...defaultProps} />);

    // Click save without making changes
    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    // Should close without API call
    expect(mockedListingsAPI.updateListing).not.toHaveBeenCalled();
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it('handles status selection', async () => {
    const user = userEvent.setup();
    render(<ListingEditModal {...defaultProps} />);

    const statusSelect = screen.getByLabelText('Status');
    await user.click(statusSelect);

    // Select inactive status
    const inactiveOption = screen.getByRole('option', { name: 'Inactive' });
    await user.click(inactiveOption);

    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockedListingsAPI.updateListing).toHaveBeenCalledWith(1, {
        status: 'inactive'
      });
    });
  });

  it('displays metrics loading state', () => {
    mockedListingsAPI.getListingMetrics.mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 1000))
    );

    render(<ListingEditModal {...defaultProps} />);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles metrics loading error', async () => {
    mockedListingsAPI.getListingMetrics.mockRejectedValue(new Error('Metrics Error'));

    render(<ListingEditModal {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Unable to load performance metrics')).toBeInTheDocument();
    });
  });

  it('does not render when listing is null', () => {
    const props = { ...defaultProps, listing: null };
    const { container } = render(<ListingEditModal {...props} />);

    expect(container.firstChild).toBeNull();
  });

  it('applies correct stock status colors', async () => {
    const outOfStockMetrics = { ...mockMetrics, stock_status: 'out_of_stock' };
    mockedListingsAPI.getListingMetrics.mockResolvedValue(outOfStockMetrics);

    render(<ListingEditModal {...defaultProps} />);

    await waitFor(() => {
      const stockChip = screen.getByText('OUT OF STOCK');
      expect(stockChip).toHaveClass('MuiChip-colorError');
    });
  });

  it('applies correct price competitiveness colors', async () => {
    const needsReviewMetrics = { ...mockMetrics, price_competitiveness: 'needs_review' };
    mockedListingsAPI.getListingMetrics.mockResolvedValue(needsReviewMetrics);

    render(<ListingEditModal {...defaultProps} />);

    await waitFor(() => {
      const priceChip = screen.getByText('NEEDS REVIEW');
      expect(priceChip).toHaveClass('MuiChip-colorError');
    });
  });

  it('validates title length', async () => {
    const user = userEvent.setup();
    render(<ListingEditModal {...defaultProps} />);

    const titleField = screen.getByDisplayValue('Test Product');
    await user.clear(titleField);
    await user.type(titleField, 'A'.repeat(256)); // Too long

    const saveButton = screen.getByText('Save Changes');
    await user.click(saveButton);

    expect(screen.getByText('Title must be less than 255 characters')).toBeInTheDocument();
  });
});