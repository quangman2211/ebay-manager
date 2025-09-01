import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Orders from '../Orders';
import OrderDataService from '../../services/OrderDataService';
import { createMockOrder } from '../../test-utils';

// Mock axios first (before any imports that use it)
jest.mock('axios', () => ({
  __esModule: true,
  default: {
    create: jest.fn(() => ({
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
    })),
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

// Mock the API modules
jest.mock('../../services/api', () => ({
  accountsAPI: {
    getAccounts: jest.fn(),
  },
}));
jest.mock('../../services/OrderDataService');

const { accountsAPI } = require('../../services/api');

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('Orders Page - Select All Bug', () => {
  const mockAccounts = [
    { id: 1, name: 'Account 1', username: 'user1' },
  ];

  const mockOrders = [
    createMockOrder({ 
      id: 1, 
      item_id: 'ORDER-001',
      csv_row: { 'Order Number': 'ORDER-001', 'Buyer Username': 'buyer1' }
    }),
    createMockOrder({ 
      id: 2, 
      item_id: 'ORDER-002',
      csv_row: { 'Order Number': 'ORDER-002', 'Buyer Username': 'buyer2' }
    }),
    createMockOrder({ 
      id: 3, 
      item_id: 'ORDER-003',
      csv_row: { 'Order Number': 'ORDER-003', 'Buyer Username': 'buyer3' }
    }),
    createMockOrder({ 
      id: 4, 
      item_id: 'ORDER-004',
      csv_row: { 'Order Number': 'ORDER-004', 'Buyer Username': 'buyer4' }
    }),
    createMockOrder({ 
      id: 5, 
      item_id: 'ORDER-005',
      csv_row: { 'Order Number': 'ORDER-005', 'Buyer Username': 'buyer5' }
    }),
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    accountsAPI.getAccounts.mockResolvedValue(mockAccounts);
    OrderDataService.fetchOrders.mockResolvedValue(mockOrders);
    OrderDataService.bulkUpdateOrderStatus.mockResolvedValue({
      successful: [],
      failed: [],
      totalProcessed: 0,
      errors: [],
    });
  });

  it('should select all orders when header checkbox is clicked', async () => {
    renderWithTheme(<Orders />);

    // Wait for orders to load
    await waitFor(() => {
      expect(screen.getByText('ORDER-001')).toBeInTheDocument();
    });

    // Find the header checkbox (first checkbox in the DataGrid)
    const checkboxes = screen.getAllByRole('checkbox');
    const headerCheckbox = checkboxes[0]; // First checkbox is the header select-all

    // Initially, no orders should be selected
    expect(screen.getByText('0 orders selected')).toBeInTheDocument();

    // Click the header checkbox to select all
    fireEvent.click(headerCheckbox);

    // All orders should be selected
    await waitFor(() => {
      expect(screen.getByText('5 orders selected')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify bulk operations toolbar is active
    const updateButton = screen.getByRole('button', { name: /update status/i });
    expect(updateButton).toBeInTheDocument();
  });

  it('should handle rapid select-all operations (mobile simulation)', async () => {
    renderWithTheme(<Orders />);

    // Wait for orders to load
    await waitFor(() => {
      expect(screen.getByText('ORDER-001')).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole('checkbox');
    const headerCheckbox = checkboxes[0];

    // Simulate rapid clicking (common on mobile with touch events)
    fireEvent.click(headerCheckbox);
    fireEvent.click(headerCheckbox);
    fireEvent.click(headerCheckbox);

    // After odd number of clicks, all should be selected
    await waitFor(() => {
      expect(screen.getByText('5 orders selected')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should maintain selection state during mobile viewport resize', async () => {
    // Set mobile viewport
    global.innerWidth = 375;
    global.innerHeight = 667;
    global.dispatchEvent(new Event('resize'));

    renderWithTheme(<Orders />);

    // Wait for orders to load
    await waitFor(() => {
      expect(screen.getByText('ORDER-001')).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole('checkbox');
    const headerCheckbox = checkboxes[0];

    // Select all
    fireEvent.click(headerCheckbox);

    // Verify selection
    await waitFor(() => {
      expect(screen.getByText('5 orders selected')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Simulate viewport change (orientation change on mobile)
    global.innerWidth = 667;
    global.innerHeight = 375;
    global.dispatchEvent(new Event('resize'));

    // Selection should be maintained
    expect(screen.getByText('5 orders selected')).toBeInTheDocument();
  });

  it('should properly sync bulk selection hook with DataGrid selection model', async () => {
    renderWithTheme(<Orders />);

    // Wait for orders to load
    await waitFor(() => {
      expect(screen.getByText('ORDER-001')).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole('checkbox');
    const headerCheckbox = checkboxes[0];

    // Select all via header checkbox
    fireEvent.click(headerCheckbox);

    // Wait for selection to complete
    await waitFor(() => {
      expect(screen.getByText('5 orders selected')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Clear selection button should work
    const clearButton = screen.getByRole('button', { name: /clear selection/i });
    fireEvent.click(clearButton);

    // Should return to 0 selected
    await waitFor(() => {
      expect(screen.getByText('0 orders selected')).toBeInTheDocument();
    });
  });
});